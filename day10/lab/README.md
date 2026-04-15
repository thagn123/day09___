# Lab Day 10 — Data Pipeline & Data Observability

**Môn:** AI in Action (AICB-P1)  
**Học viên:** Đào Quang Thắng  
**Tiếp nối:** Day 08 RAG · Day 09 Multi-agent — cùng case CS + IT Helpdesk

---

## Cài đặt

```bash
# 1. Di chuyển vào thư mục lab (BẮT BUỘC chạy tất cả lệnh từ đây)
cd day10/lab

# 2. Tạo file .env
cp .env.example .env

# 3. Cài dependencies
python -m pip install -r requirements.txt
```

> **Lưu ý Windows:** Thêm `$env:PYTHONIOENCODING="utf-8"` trước khi chạy để tránh lỗi encoding.

---

## Thứ tự chạy

### Bước 1 — Pipeline chuẩn (ingest → clean → validate → embed)

```bash
python etl_pipeline.py run
```

Kết quả mong đợi:
- `raw_records=10`, `cleaned_records=6`, `quarantine_records=4`
- 8 expectations đều `OK`
- `PIPELINE_OK`

---

### Bước 2 — Kiểm tra freshness

```bash
python etl_pipeline.py freshness --manifest artifacts/manifests/manifest_<run-id>.json
```

> `freshness_check=FAIL` là bình thường với data mẫu (exported_at cũ ~5 ngày). Giải thích trong `docs/runbook.md`.

---

### Bước 3 — Eval retrieval (sau khi đã embed)

```bash
python eval_retrieval.py --out artifacts/eval/before_after_eval.csv
```

Kết quả mong đợi: tất cả câu `contains_expected=yes`, `hits_forbidden=no`.

---

### Bước 4 — Inject corruption (Sprint 3 — before/after evidence)

```bash
# Inject: tắt fix refund, bỏ qua halt
python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate

# Eval sau inject → hits_forbidden=yes cho câu refund (đây là "before")
python eval_retrieval.py --out artifacts/eval/after_inject_bad.csv

# Chạy lại pipeline chuẩn để restore
python etl_pipeline.py run --run-id final-clean

# Eval sau restore → hits_forbidden=no (đây là "after")
python eval_retrieval.py --out artifacts/eval/before_after_eval.csv
```

---

### Bước 5 — Kiểm tra idempotency

```bash
# Chạy lần 2 → embed_upsert count vẫn = 6, không có embed_prune_removed
python etl_pipeline.py run --run-id rerun-check
```

---

### Bước 6 — Grading (sau khi BTC public file lúc 17:00)

```bash
python grading_run.py --out artifacts/eval/grading_run.jsonl
```

---

### Bước 7 — Kiểm tra nhanh artifact (tuỳ chọn)

```bash
python instructor_quick_check.py --grading artifacts/eval/grading_run.jsonl
python instructor_quick_check.py --manifest artifacts/manifests/manifest_<run-id>.json
```

---

## Cấu trúc thư mục quan trọng

```
lab/
├── etl_pipeline.py           # Entrypoint: run | freshness
├── eval_retrieval.py         # Eval before/after (retrieval + keyword)
├── grading_run.py            # Grading JSONL (chạy sau 17:00)
├── instructor_quick_check.py # Sanity check artifact
│
├── transform/
│   └── cleaning_rules.py     # 9 cleaning rules (6 baseline + 3 mới)
├── quality/
│   └── expectations.py       # 8 expectations (6 baseline + 2 mới)
├── monitoring/
│   └── freshness_check.py    # SLA freshness check
├── contracts/
│   └── data_contract.yaml    # Owner, SLA, canonical sources
│
├── data/
│   ├── raw/policy_export_dirty.csv   # Raw export có lỗi cố ý
│   ├── docs/                         # 5 tài liệu policy
│   └── test_questions.json           # 4 câu golden retrieval
│
├── artifacts/
│   ├── cleaned/              # CSV sau clean
│   ├── quarantine/           # CSV bị loại (với reason)
│   ├── manifests/            # JSON manifest mỗi run (có run_id)
│   └── eval/                 # Kết quả eval retrieval
│
├── docs/
│   ├── pipeline_architecture.md  # Sơ đồ + bảng trách nhiệm
│   ├── data_contract.md          # Source map + schema
│   ├── runbook.md                # Incident handling (5 mục)
│   └── quality_report.md         # Số liệu + before/after evidence
│
└── reports/
    ├── group_report.md
    └── individual/Đào Quang Thắng.md
```

---

## Cleaning rules mới (Sprint 2)

| Rule | Mô tả | metric_impact |
|------|-------|---------------|
| **R1: BOM strip** | Xóa BOM `\ufeff` và zero-width chars | Phát hiện khi inject BOM vào CSV |
| **R2: Whitespace normalize** | Collapse multi-space/tab/newline | Giảm duplicate miss |
| **R3: Min meaningful content** | Quarantine chunk < 10 ký tự alphanum | Lọc chunk gần-rỗng |

## Expectations mới (Sprint 2)

| Expectation | Severity | Mô tả |
|-------------|----------|-------|
| **E7: unique_chunk_id** | halt | Không có duplicate chunk_id (đảm bảo idempotency) |
| **E8: no_bom_zero_width_chars** | warn | Không còn BOM trong cleaned text |

---

## Before / After Evidence

| Câu hỏi | Metric | inject-bad | final-clean |
|---------|--------|------------|-------------|
| `q_refund_window` | `hits_forbidden` | **yes** ❌ | **no** ✅ |
| `q_leave_version` | `top1_doc_expected` | yes | yes |

→ Xem `artifacts/eval/after_inject_bad.csv` vs `artifacts/eval/before_after_eval.csv`

---

## Debug order (slide Day 10)

```
Freshness → Volume & errors → Schema & contract → Lineage/run_id → mới đến model/prompt
```

## Tài nguyên

- Slide: [`../lecture-10.html`](../lecture-10.html)
- Scoring: [`SCORING.md`](SCORING.md)
- Lab Day 09: [`../../day09/lab/README.md`](../../day09/lab/README.md)
