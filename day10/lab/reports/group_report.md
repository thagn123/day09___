# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** Nhóm Day 10  
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| Đào Quang Thắng | **Ingestion Owner** + **Monitoring / Docs Owner** | thang.dao@student |
| Phạm Hải Đăng | **Embed Owner** (Chroma collection, idempotency, eval) | dang.pham@student |
| Phạm Hoàng Kim Liên | **Cleaning / Quality Owner** (cleaning_rules.py, expectations.py, quarantine) | lien.pham@student |

**Ngày nộp:** 2026-04-15  
**Repo:** Lecture-Day-08-09-10-main  
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Nộp tại:** `reports/group_report.md`  
> **Deadline commit:** xem `SCORING.md` (code/trace sớm; report có thể muộn hơn nếu được phép).  
> Phải có **run_id**, **đường dẫn artifact**, và **bằng chứng before/after** (CSV eval hoặc screenshot).

---

## 1. Pipeline tổng quan (150–200 từ)

Nguồn raw là file CSV mẫu `data/raw/policy_export_dirty.csv` — mô phỏng export từ hệ thống CRM/HR nội bộ với 10 dòng chứa nhiều loại lỗi: duplicate chunk, doc_id ngoài allowlist (`legacy_catalog_xyz_zzz`), ngày không ISO (`01/02/2026`), chunk rỗng, HR policy cũ (2025, "10 ngày phép năm"), và stale refund window ("14 ngày" từ policy v3).

Pipeline chạy end-to-end qua 4 bước: **ingest** (đọc CSV raw) → **clean** (áp dụng 9 cleaning rules) → **validate** (chạy 8 expectations) → **embed** (upsert vào ChromaDB collection `day10_kb` + prune stale vectors). Mỗi run tạo `run_id` ghi trong log + manifest JSON để truy vết.

**Tóm tắt luồng:**

raw CSV → `load_raw_csv()` → `clean_rows()` → cleaned CSV + quarantine CSV → `run_expectations()` → halt/pass → `cmd_embed_internal()` (upsert + prune) → manifest + freshness check

**Lệnh chạy một dòng:**

```bash
$env:PYTHONIOENCODING="utf-8"; py etl_pipeline.py run --run-id final-clean
```

`run_id` được ghi ở dòng đầu log: `run_id=final-clean` và trong `artifacts/manifests/manifest_final-clean.json`.

---

## 2. Cleaning & expectation (150–200 từ)

Baseline đã có 6 rule (allowlist doc_id, parse ngày ISO/DMY, quarantine HR cũ, fix refund 14→7, dedupe, loại chunk rỗng) và 6 expectation (min_one_row, no_empty_doc_id, refund_no_stale_14d_window, chunk_min_length_8, effective_date_iso, hr_leave_no_stale_10d_annual).

Tôi thêm **3 rule mới** và **2 expectation mới**:

### 2a. Bảng metric_impact (bắt buộc — chống trivial)

| Rule / Expectation mới (tên ngắn) | Trước (số liệu) | Sau / khi inject (số liệu) | Chứng cứ (log / CSV / commit) |
|-----------------------------------|------------------|-----------------------------|-------------------------------|
| R1: BOM/zero-width strip | Nếu inject BOM: chunk_text chứa `\ufeff` | Sau clean: BOM bị loại, text sạch | `cleaning_rules.py` — Phạm Hoàng Kim Liên |
| R2: Whitespace normalize | chunk có multi-space/tab: dedupe miss | Sau normalize: collapse → dedupe chính xác hơn | `cleaning_rules.py` — Phạm Hoàng Kim Liên |
| R3: Minimum meaningful content (≤10 alphanum) | chunk gần-rỗng lọt qua "missing_chunk_text" | quarantine thêm dòng `insufficient_meaningful_content` | `cleaning_rules.py` — Phạm Hoàng Kim Liên |
| E7: unique_chunk_id (halt) | Nếu inject duplicate chunk_id: upsert mất data | halt pipeline, `duplicate_chunk_ids>0` | `expectations.py` — Phạm Hoàng Kim Liên |
| E8: no_bom_zero_width_chars (warn) | Sau inject BOM vẫn còn trong cleaned | warn, `rows_with_bom>0` | `expectations.py` — Phạm Hoàng Kim Liên |

**Rule chính (baseline + mở rộng):**

- Baseline: allowlist doc_id, parse DD/MM/YYYY→ISO, quarantine HR<2026, fix refund 14→7, dedupe text, loại chunk rỗng
- Mới: BOM strip (R1), whitespace normalize (R2), minimum content filter (R3)

**Ví dụ 1 lần expectation fail và cách xử lý:**

Khi chạy `--no-refund-fix --skip-validate`: expectation `refund_no_stale_14d_window` **FAIL** (violations=1). Pipeline warn nhưng vẫn embed vì `--skip-validate`. Eval sau đó cho thấy `hits_forbidden=yes` cho câu refund. Chạy lại pipeline chuẩn → expectation OK → `hits_forbidden=no`.

---

## 3. Before / after ảnh hưởng retrieval hoặc agent (200–250 từ)

**Kịch bản inject:** Sprint 3 — chạy `py etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate` để cố ý embed chunk stale "14 ngày làm việc" vào ChromaDB.

**Kết quả định lượng:**

| Câu hỏi | Metric | inject-bad (before) | final-clean (after) |
|---------|--------|---------------------|---------------------|
| `q_refund_window` | `contains_expected` | yes | yes |
| `q_refund_window` | `hits_forbidden` | **yes** ❌ | **no** ✅ |
| `q_leave_version` | `contains_expected` | yes | yes |
| `q_leave_version` | `hits_forbidden` | no | no |
| `q_leave_version` | `top1_doc_expected` | yes | yes |
| `q_p1_sla` | `contains_expected` | yes | yes |
| `q_lockout` | `contains_expected` | yes | yes |

**Phân tích:** Khi inject (tắt fix refund), chunk "14 ngày làm việc" lọt vào top-k retrieval → `hits_forbidden=yes`. Agent sẽ trích dẫn thông tin sai. Sau khi chạy pipeline chuẩn: rule fix 14→7 hoạt động, embed prune xóa vector stale (`embed_prune_removed=1`), eval trở lại sạch.

Câu `q_leave_version` ổn định ở cả 2 kịch bản vì rule quarantine HR cũ luôn bật (không bị tắt bởi `--no-refund-fix`), chứng minh cleaning rule versioning hoạt động hiệu quả.

Artifact: `artifacts/eval/after_inject_bad.csv`, `artifacts/eval/before_after_eval.csv`

---

## 4. Freshness & monitoring (100–150 từ)

**SLA chọn:** 24 giờ (`FRESHNESS_SLA_HOURS=24` trong `.env`). Ý nghĩa: corpus phải được cập nhật trong vòng 24h kể từ lần export cuối.

**Kết quả:** `freshness_check=FAIL` — `age_hours=118.5`, vượt SLA 24h.

Đây là **FAIL hợp lý trên data mẫu**: CSV mẫu có `exported_at=2026-04-10T08:00:00` (cách hiện tại ~5 ngày). Trong production, pipeline chạy hàng ngày với export mới → sẽ PASS.

Freshness đo tại boundary `publish` (sau embed) — đọc `latest_exported_at` từ manifest. Nếu cần đo 2 boundary (ingest + publish), cần thêm timestamp vào log ở bước ingest.

---

## 5. Liên hệ Day 09 (50–100 từ)

Pipeline Day 10 xử lý cùng domain tài liệu với Day 09 (policy_refund_v4, sla_p1_2026, it_helpdesk_faq, hr_leave_policy). Tuy nhiên, **tách collection** `day10_kb` để tránh xung đột khi thí nghiệm inject/clean. Nếu cần tích hợp, đổi `CHROMA_COLLECTION` trong `.env` hoặc export cleaned CSV sang `day09/lab/data/docs/`.

---

## 6. Rủi ro còn lại & việc chưa làm

- Bộ dữ liệu chỉ 10 rows — chưa đủ cho distribution monitoring có ý nghĩa thống kê.
- Freshness chỉ đo 1 boundary (publish), chưa tách ingest boundary.
- Chưa có LLM-judge eval end-to-end.
- Encoding Windows (cp1252) cần workaround `PYTHONIOENCODING=utf-8`.
- Chưa tích hợp scheduler/cron tự động.
