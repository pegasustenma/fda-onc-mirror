# fda-onc-mirror

FDA [Oncology/Hematologic Malignancies Approval Notifications](https://www.fda.gov/drugs/resources-information-approved-drugs/oncology-cancerhematologic-malignancies-approval-notifications) 表格的定时镜像。GitHub Actions 每日两次（JST 06:17 / 18:17）抓取。

- `notifications.tsv`：`date`(ISO) / `title` / `desc`，按日期倒序；只在抓取成功时覆盖。
- `meta.json`：`last_success_jst` / `last_attempt_jst` / `http_status` / `rows` / `latest_row_date` / `doc_modified` / `last_error`。

仅含 FDA 公开数据。下游消费方：Harumoni `scripts/hm_core.py al4b`（镜像优先，直连 FDA 作为回退）。
