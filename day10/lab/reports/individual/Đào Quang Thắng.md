# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Đào Quang Thắng  
**Vai trò:** Ingestion Owner + Monitoring / Docs Owner  
**Ngày nộp:** 2026-04-15  
**Độ dài yêu cầu:** **400–650 từ**

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- `etl_pipeline.py` — phần `load_raw_csv()`, `cmd_run()` (logging `raw_records`, `cleaned_records`, `quarantine_records`), tạo `manifest_<run_id>.json`
- `data/raw/policy_export_dirty.csv` — định nghĩa raw path đầu vào
- `monitoring/freshness_check.py` — đọc manifest, tính `age_hours`, so sánh SLA
- `docs/pipeline_architecture.md` — sơ đồ Mermaid + bảng trách nhiệm
- `docs/data_contract.md` — source map (≥2 nguồn) + schema + quarantine rules
- `docs/runbook.md` — 5 mục Symptom → Prevention
- `docs/quality_report.md` — số liệu thực + before/after evidence
- `reports/group_report.md` — báo cáo nhóm

**Kết nối với thành viên khác:** Sau khi tôi ingest raw → Phạm Hoàng Kim Liên clean + validate → Phạm Hải Đăng embed → tôi lấy manifest để check freshness.

**Bằng chứng:** log `run_id=final-clean` trong `artifacts/logs/run_final-clean.log`, manifest `artifacts/manifests/manifest_final-clean.json`.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

**Quyết định:** Thiết kế `run_id` là timestamp UTC (`2026-04-15T08-11Z`) thay vì số tăng dần.

**Bối cảnh:** Pipeline chạy nhiều lần (chuẩn, inject, restore, rerun). Cần phân biệt rõ từng run để trace artifact.

**Lý do chọn timestamp:** Số tăng dần (`run_001`, `run_002`) bị reset nếu xóa log. Timestamp UTC có thể sort theo thời gian, dễ tìm run gần nhất (`manifest_2026-04-15T08-11Z.json`), không cần state lưu trữ riêng. Tên file log/manifest/cleaned/quarantine đều dùng `run_id` → tìm artifact của 1 run là tìm tất cả bằng 1 pattern.

Ngoài ra: timestamp `exported_at` trong manifest dùng để tính freshness SLA — đây là `latest_exported_at` lấy từ `max(r["exported_at"])` trong cleaned rows, đảm bảo đo đúng boundary `publish` chứ không phải `ingest`.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

**Triệu chứng:** Khi chạy với Anaconda Python từ thư mục cha (`Lecture-Day-08-09-10-main`), `eval_retrieval.py` báo lỗi:
```
Collection error: Collection [day10_kb] does not exist
```

**Metric phát hiện:** Error message rõ ràng — ChromaDB tìm `./chroma_db` tính từ working directory hiện tại (thư mục cha), không phải `day10/lab/`.

**Nguyên nhân:** `CHROMA_DB_PATH=./chroma_db` là đường dẫn tương đối trong `.env`. Script dùng `load_dotenv()` nhưng `.env` chỉ tồn tại trong `day10/lab/`, nên khi chạy từ thư mục cha, `chroma_db` không được tìm thấy.

**Fix:**
```powershell
cd "day10/lab"   # BẮT BUỘC trước khi chạy bất kỳ script nào
```

Sau fix: collection tìm thấy, eval chạy thành công. Ghi chú vào README: "Di chuyển vào thư mục lab (BẮT BUỘC chạy tất cả lệnh từ đây)".

---

## 4. Bằng chứng trước / sau (80–120 từ)

**run_id inject:** `inject-bad` | **run_id clean:** `final-clean`

Trích từ `artifacts/eval/after_inject_bad.csv`:
```
q_refund_window | top1_doc_id=policy_refund_v4 | contains_expected=yes | hits_forbidden=YES
```

Trích từ `artifacts/eval/before_after_eval.csv`:
```
q_refund_window | top1_doc_id=policy_refund_v4 | contains_expected=yes | hits_forbidden=no
```

**Giải thích:** Khi inject (`--no-refund-fix`), chunk stale "14 ngày làm việc" embed vào ChromaDB, lọt vào top-k → `hits_forbidden=YES`. Sau restore pipeline chuẩn: manifest `run_id=final-clean` ghi `no_refund_fix=false`, `embed_prune_removed=1` → chunk stale bị xóa → `hits_forbidden=no`.

Freshness manifest `final-clean`: `freshness_check=FAIL`, `age_hours=118.5` — FAIL hợp lý (data mẫu, giải thích trong runbook).

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ triển khai **freshness đo 2 boundary**: thêm timestamp `ingest_done_at` vào log ngay sau `load_raw_csv()`, và `publish_done_at` sau `embed_upsert`. Manifest sẽ ghi cả 2 mốc → `freshness_check()` tính được latency tách biệt ingest vs embed, phát hiện bottleneck chính xác hơn. Đây là điều kiện để đạt Distinction (b) và bonus +1 điểm theo SCORING.
