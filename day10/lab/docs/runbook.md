# Runbook — Lab Day 10 (incident tối giản)

---

## Symptom

Agent trả lời sai policy hoàn tiền: "Khách hàng có **14 ngày làm việc** để yêu cầu hoàn tiền" — thực tế policy v4 quy định **7 ngày làm việc**. User/QA phản hồi câu trả lời không khớp tài liệu chính thức.

Biến thể khác: agent trả lời "nhân viên được 10 ngày phép năm" thay vì 12 ngày (bản HR 2026).

---

## Detection

| Metric / signal | Giá trị bình thường | Giá trị khi incident |
|-----------------|---------------------|---------------------|
| `freshness_check` (manifest) | PASS (age ≤ 24h) | FAIL — `age_hours > 24`, `reason: freshness_sla_exceeded` |
| `expectation[refund_no_stale_14d_window]` | OK | **FAIL** — `violations=1` (chunk chứa "14 ngày làm việc") |
| `eval_retrieval.py` → `hits_forbidden` cho `q_refund_window` | `no` | **`yes`** — top-k chứa chunk stale |
| `embed_prune_removed` trong log | 0 | > 0 nếu vector cũ còn tồn tại |

**Phát hiện nhanh:** Chạy `py eval_retrieval.py --out artifacts/eval/check.csv` → kiểm tra cột `hits_forbidden`.

---

## Diagnosis

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|------------------|
| 1 | Kiểm tra `artifacts/manifests/manifest_<run_id>.json` — xem `no_refund_fix`, `skipped_validate` | Nếu `no_refund_fix=true` → pipeline đã bỏ qua rule fix 14→7 |
| 2 | Mở `artifacts/quarantine/quarantine_<run_id>.csv` — đếm rows và reasons | Nếu thiếu dòng `stale_hr_policy_effective_date` → HR cũ lọt vào cleaned |
| 3 | Mở `artifacts/cleaned/cleaned_<run_id>.csv` — tìm "14 ngày làm việc" | Nếu có → rule fix refund bị tắt hoặc pattern không match |
| 4 | Chạy `py eval_retrieval.py --out artifacts/eval/diag.csv` | Xem `top1_preview` và `hits_forbidden` cho câu refund |
| 5 | Kiểm tra Chroma collection count: `col.count()` | So sánh với `cleaned_records` — nếu lệch → stale vectors còn |

**Timebox:** 0–5' freshness/manifest → 5–12' cleaned CSV + quarantine → 12–20' eval + Chroma count. Hết 20' → mitigate.

---

## Mitigation

1. **Rerun pipeline chuẩn** (không flag inject):
   ```bash
   $env:PYTHONIOENCODING="utf-8"
   py etl_pipeline.py run --run-id hotfix-<timestamp>
   ```
   Pipeline sẽ: fix refund 14→7, quarantine HR cũ, prune stale vectors, upsert cleaned.

2. **Kiểm chứng ngay:**
   ```bash
   py eval_retrieval.py --out artifacts/eval/after_hotfix.csv
   ```
   Confirm: `hits_forbidden=no`, `contains_expected=yes`.

3. **Nếu không thể rerun ngay:** Tạm thông báo user "Dữ liệu policy đang được cập nhật — xin kiểm tra lại sau 1 giờ" (banner/disclaimer trên UI agent).

---

## Prevention

1. **Expectation halt:** Giữ `refund_no_stale_14d_window` và `hr_leave_no_stale_10d_annual` ở severity `halt` — pipeline tự dừng nếu data sai.
2. **Freshness alert:** Thiết lập cron chạy `py etl_pipeline.py freshness --manifest ...` mỗi giờ; alert khi FAIL.
3. **Scheduled re-embed:** Cron job chạy pipeline hàng ngày để đảm bảo corpus luôn tươi.
4. **Owner trên contract:** Điền `owner_team` trong `contracts/data_contract.yaml` — khi alert, biết ai chịu trách nhiệm fix.
5. **Golden eval tự động:** Tích hợp `eval_retrieval.py` vào CI/CD — chạy sau mỗi lần pipeline publish; fail nếu `hits_forbidden=yes`.
