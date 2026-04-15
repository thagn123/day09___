# Data contract — Lab Day 10

> Bắt đầu từ `contracts/data_contract.yaml` — mở rộng và đồng bộ file này.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| CSV export từ DB nội bộ (`data/raw/policy_export_dirty.csv`) | Batch CSV — đọc file export định kỳ từ hệ thống CRM/HR | Schema drift (thêm/mất cột), encoding lỗi (BOM), duplicate rows, ngày không ISO, doc_id ngoài allowlist | `raw_records` count, `quarantine_records` count, expectation `refund_no_stale_14d_window` |
| Tài liệu policy nội bộ (`data/docs/*.txt`) | File text trên shared storage — đọc trực tiếp khi cần re-embed | File bị đổi tên/xóa không thông báo, version conflict (cùng tên khác nội dung), encoding UTF-8 vs legacy | Content hash so sánh giữa các lần sync, `effective_date` trong metadata |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | Hash ổn định từ `doc_id + chunk_text + seq` — dùng cho upsert idempotent |
| doc_id | string | Có | Phải thuộc allowlist trong `data_contract.yaml` (`policy_refund_v4`, `sla_p1_2026`, `it_helpdesk_faq`, `hr_leave_policy`) |
| chunk_text | string | Có | Tối thiểu 8 ký tự (expectation E4), tối thiểu 10 ký tự alphanum thực (rule R3) |
| effective_date | date (YYYY-MM-DD) | Có | Chuẩn hóa từ nhiều format (ISO, DD/MM/YYYY). HR policy phải ≥ 2026-01-01 |
| exported_at | datetime | Có | Timestamp export từ hệ nguồn — dùng tính freshness SLA |

---

## 3. Quy tắc quarantine vs drop

**Quarantine (không drop):** Mọi record bị loại đều được lưu vào `artifacts/quarantine/quarantine_<run_id>.csv` kèm cột `reason`. Các lý do quarantine:

| Reason | Mô tả | Quyết định |
|--------|--------|-----------|
| `unknown_doc_id` | doc_id không thuộc allowlist | Quarantine — cần review thủ công |
| `missing_effective_date` | Không có ngày hiệu lực | Quarantine — không embed vì thiếu metadata |
| `invalid_effective_date_format` | Ngày không parse được | Quarantine — cần sửa format |
| `stale_hr_policy_effective_date` | HR policy trước 2026-01-01 (bản cũ) | Quarantine — conflict version |
| `missing_chunk_text` | Nội dung rỗng | Quarantine — không có giá trị embed |
| `duplicate_chunk_text` | Trùng nội dung (giữ bản đầu) | Quarantine — tránh duplicate retrieval |
| `insufficient_meaningful_content` | Ít hơn 10 ký tự alphanum | Quarantine — chunk gần rỗng |

**Không silent drop:** Pipeline không xóa bỏ record nào mà không ghi log. Mọi quarantine đều có `run_id` để truy vết.

**Approve merge lại:** Data Owner review `quarantine.csv`, sửa source nếu cần, và chạy lại pipeline.

---

## 4. Phiên bản & canonical

**Source of truth cho policy refund:** `data/docs/policy_refund_v4.txt` — phiên bản 4, effective_date 2026-02-01.

- Cửa sổ hoàn tiền chính xác: **7 ngày làm việc** (không phải 14 ngày từ v3 cũ).
- CSV export có thể chứa chunk từ migration cũ (v3) với "14 ngày" → pipeline clean phải fix thành 7 ngày.
- Version bump: khi policy thay đổi, cập nhật `data_contract.yaml` field `canonical_sources` + allowlist + cleaning rules.

**Source of truth cho HR leave:** `data/docs/hr_leave_policy.txt` — chính sách 2026, 12 ngày phép/năm (< 3 năm KN). Bản 2025 (10 ngày) phải được quarantine.
