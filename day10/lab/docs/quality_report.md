# Quality report — Lab Day 10 (nhóm)

**run_id:** `final-clean` (pipeline chuẩn cuối) / `inject-bad` (inject corruption Sprint 3)  
**Ngày:** 2026-04-15

---

## 1. Tóm tắt số liệu

| Chỉ số | Trước (inject-bad) | Sau (final-clean) | Ghi chú |
|--------|---------------------|---------------------|---------|
| raw_records | 10 | 10 | Cùng file CSV raw |
| cleaned_records | 6 | 6 | Số lượng bằng nhau nhưng nội dung khác (14 vs 7 ngày) |
| quarantine_records | 4 | 4 | Quarantine: unknown_doc_id(1), missing fields(2), stale HR(1) |
| Expectation halt? | **FAIL** (`refund_no_stale_14d_window`) | Không (tất cả OK) | `--skip-validate` cho phép embed data xấu |

---

## 2. Before / after retrieval (bắt buộc)

> Đính kèm: `artifacts/eval/after_inject_bad.csv` (before) và `artifacts/eval/before_after_eval.csv` (after).

**Câu hỏi then chốt:** refund window (`q_refund_window`)

**Trước (inject-bad — `--no-refund-fix --skip-validate`):**
```
q_refund_window | top1_doc_id=policy_refund_v4 | contains_expected=yes | hits_forbidden=YES
```
→ Top-k chứa chunk stale "14 ngày làm việc" — agent sẽ trích dẫn thông tin sai.

**Sau (final-clean — pipeline chuẩn):**
```
q_refund_window | top1_doc_id=policy_refund_v4 | contains_expected=yes | hits_forbidden=no
```
→ Chunk stale đã được fix (14→7) + prune vector cũ. Agent trả lời đúng "7 ngày làm việc".

**Merit: versioning HR — `q_leave_version`**

**Trước (inject-bad):**
```
q_leave_version | top1_doc_id=hr_leave_policy | contains_expected=yes | hits_forbidden=no | top1_doc_expected=yes
```

**Sau (final-clean):**
```
q_leave_version | top1_doc_id=hr_leave_policy | contains_expected=yes | hits_forbidden=no | top1_doc_expected=yes
```
→ Câu HR leave ổn định cả trước và sau vì rule quarantine HR cũ (effective_date < 2026-01-01) luôn bật — bản "10 ngày phép năm" bị quarantine ở cả 2 run. Điều này chứng minh cleaning rule `stale_hr_policy_effective_date` hoạt động hiệu quả.

---

## 3. Freshness & monitor

**SLA chọn:** 24 giờ (FRESHNESS_SLA_HOURS=24 trong `.env`).

**Kết quả:** `freshness_check=FAIL` — `age_hours=118.5`, vượt SLA 24h.

**Giải thích:** File CSV mẫu có `exported_at=2026-04-10T08:00:00` (cách hiện tại ~5 ngày). Đây là data mẫu snapshot, không phải export thời gian thực → FAIL là **đúng và mong đợi**. Trong production, pipeline sẽ chạy hàng ngày với export mới → PASS.

**Hành động nếu FAIL thật:** Kiểm tra hệ nguồn export → rerun pipeline → verify eval.

---

## 4. Corruption inject (Sprint 3)

**Kịch bản inject:** Chạy `py etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate`

- `--no-refund-fix`: Tắt rule fix "14 ngày → 7 ngày" → chunk stale policy v3 lọt vào cleaned.
- `--skip-validate`: Bỏ qua halt khi expectation `refund_no_stale_14d_window` FAIL → vẫn embed data xấu.

**Phát hiện:**
- Expectation log: `refund_no_stale_14d_window FAIL (halt) :: violations=1`
- Eval retrieval: `q_refund_window → hits_forbidden=YES`

**Recovery:** Chạy lại `py etl_pipeline.py run --run-id final-clean` → pipeline fix refund + prune stale vector + eval lại → `hits_forbidden=no`.

---

## 5. Hạn chế & việc chưa làm

- **Bộ dữ liệu nhỏ (10 rows):** Distribution monitoring (skew, anomaly) không có ý nghĩa thống kê. Cần bộ dữ liệu lớn hơn cho production.
- **Chưa có LLM-judge:** Eval chỉ dùng keyword matching, chưa kiểm tra chất lượng câu trả lời end-to-end.
- **Freshness đo 1 boundary:** Chỉ đo tại `publish` (manifest), chưa tách riêng ingest vs publish boundary.
- **Chưa tích hợp CI/CD:** Pipeline chạy manual, chưa có cron/scheduler tự động.
- **Windows encoding:** Cần `PYTHONIOENCODING=utf-8` — chưa fix được trong code (dùng workaround env var).
