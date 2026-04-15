# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Đào Quang Thắng  
**Vai trò:** Ingestion / Cleaning / Embed / Monitoring — Full-stack Pipeline Owner  
**Ngày nộp:** 2026-04-15  
**Độ dài yêu cầu:** **400–650 từ**

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- `transform/cleaning_rules.py`: Thêm 3 rule mới (R1: BOM strip, R2: whitespace normalize, R3: minimum meaningful content filter)
- `quality/expectations.py`: Thêm 2 expectation mới (E7: unique_chunk_id halt, E8: no_bom_zero_width warn)
- `docs/pipeline_architecture.md`, `docs/data_contract.md`, `docs/runbook.md`, `docs/quality_report.md`: Hoàn thiện toàn bộ documentation
- `contracts/data_contract.yaml`: Điền owner_team, alert_channel
- `reports/group_report.md`: Viết báo cáo nhóm

**Kết nối với thành viên khác:**

Làm cá nhân toàn bộ pipeline, từ ingest đến monitoring. Tiếp nối công việc Day 09 (Retrieval Worker, Policy Tool Worker) — pipeline Day 10 cung cấp corpus sạch cho multi-agent Day 09.

**Bằng chứng:** Comment trong code (line 133–153 `cleaning_rules.py`, line 115–145 `expectations.py`), log `run_id=final-clean`.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

**Quyết định:** Chọn severity **halt** cho expectation `unique_chunk_id` (E7) thay vì warn.

**Bối cảnh:** Nếu 2 cleaned rows có cùng `chunk_id`, khi upsert vào ChromaDB chỉ giữ 1 bản — mất dữ liệu âm thầm. Đây là lỗi nghiêm trọng vì agent sẽ thiếu context nhưng không ai biết.

**Lý do chọn halt:** Duplicate `chunk_id` không phải lỗi data thông thường mà là lỗi **logic pipeline** (hash collision hoặc bug trong `_stable_chunk_id`). Nếu chỉ warn, pipeline tiếp tục embed data thiếu → agent trả lời sai nghiệp vụ. Halt buộc developer phải fix root cause trước khi publish — đúng tinh thần "quality gate trước khi tốn tiền embed" (slide 9 Day 10).

So sánh: expectation E8 (BOM chars) dùng **warn** vì BOM không ảnh hưởng nghiêm trọng đến retrieval quality, chỉ là cosmetic.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

**Triệu chứng:** Khi chạy `py etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate`, pipeline crash với `UnicodeEncodeError: 'charmap' codec can't encode character '\u2192'` — ký tự mũi tên `→` trong message tiếng Việt không encode được trên Windows cp1252.

**Metric phát hiện:** Pipeline exit code ≠ 0, traceback nằm trong `etl_pipeline.py:61` (hàm `log` → `print`).

**Fix:** Thiết lập biến môi trường `PYTHONIOENCODING=utf-8` trước khi chạy:
```bash
$env:PYTHONIOENCODING="utf-8"; py etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate
```

Sau fix: pipeline inject chạy thành công → expectation `refund_no_stale_14d_window FAIL` đúng mong đợi → embed data xấu → eval cho thấy `hits_forbidden=yes` → chứng minh inject hoạt động.

---

## 4. Bằng chứng trước / sau (80–120 từ)

**run_id inject:** `inject-bad` | **run_id clean:** `final-clean`

| Câu hỏi | Metric | inject-bad | final-clean |
|---------|--------|------------|-------------|
| `q_refund_window` | `hits_forbidden` | **yes** ❌ | **no** ✅ |
| `q_refund_window` | `contains_expected` | yes | yes |

**Trước (inject-bad):** Chunk stale "14 ngày làm việc" lọt top-k → agent có thể trích dẫn sai.
**Sau (final-clean):** Rule fix 14→7 + embed prune (`embed_prune_removed=1`) → chunk stale bị xóa khỏi index → retrieval sạch.

Artifact: `artifacts/eval/after_inject_bad.csv` vs `artifacts/eval/before_after_eval.csv`

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ triển khai **freshness đo 2 boundary** (ingest timestamp + publish timestamp) với log riêng cho từng bước. Hiện tại chỉ đo tại publish (`latest_exported_at` trong manifest), chưa tách được latency giữa ingest và embed. Việc này sẽ giúp phát hiện bottleneck (ví dụ: ingest nhanh nhưng embed chậm do model load) và đạt điều kiện Distinction + bonus +1 điểm theo SCORING.
