"""FDA Oncology/Hematologic Malignancies Approval Notifications → TSV 镜像。
仅 stdlib。成功：写 notifications.tsv + meta.json；失败：只更新 meta.json 的 last_error 并 exit 1（不覆盖旧表）。
解析逻辑与 Harumoni scripts/hm_core.py::_al4b_rows 同构。"""
import json, os, re, sys, urllib.request
from datetime import datetime, timezone, timedelta

URL = ("https://www.fda.gov/drugs/resources-information-approved-drugs/"
       "oncology-cancerhematologic-malignancies-approval-notifications")
HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "notifications.tsv")
META = os.path.join(HERE, "meta.json")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
JST = timezone(timedelta(hours=9))


def clean(x):
    x = re.sub(r"<[^>]+>", " ", x)
    x = x.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#39;", "'")
    return re.sub(r"\s+", " ", x).strip()


def parse(html):
    out = []
    for tr in re.findall(r"<tr>(.*?)</tr>", html, re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 3:
            continue
        t, d, ds = clean(tds[0]), clean(tds[1]), clean(tds[2])
        m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", ds)
        if not m:
            continue
        out.append((f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}", t, d))
    return out


def load_meta():
    try:
        with open(META, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_meta(meta):
    with open(META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    now = datetime.now(JST).isoformat(timespec="seconds")
    meta = load_meta()
    meta["last_attempt_jst"] = now
    req = urllib.request.Request(URL, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            status = r.status
            html = r.read().decode("utf-8", "ignore")
    except Exception as e:
        meta["last_error"] = f"{now} {type(e).__name__}: {e}"
        save_meta(meta)
        print(f"FETCH FAIL: {meta['last_error']}")
        return 1
    rows = parse(html)
    if not rows:
        meta["last_error"] = f"{now} HTTP {status} but table parse=0 (page structure changed?)"
        save_meta(meta)
        print(f"PARSE FAIL: {meta['last_error']}")
        return 1
    mdt = re.search(r'"article:modified_time"\s+content="([^"]+)"', html) or \
          re.search(r'article:modified_time[^0-9]*([0-9/]{8,10})', html)
    rows.sort(key=lambda r: r[0], reverse=True)
    with open(TSV, "w", encoding="utf-8", newline="\n") as f:
        f.write("date\ttitle\tdesc\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    meta.update({"source_url": URL, "last_success_jst": now, "http_status": status,
                 "doc_modified": mdt.group(1).strip() if mdt else "", "rows": len(rows),
                 "latest_row_date": rows[0][0], "last_error": ""})
    save_meta(meta)
    print(f"OK HTTP {status} rows={len(rows)} latest={rows[0][0]} doc_modified={meta['doc_modified']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
