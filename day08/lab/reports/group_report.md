# Báo cáo Nhóm — Lab Day 08: RAG Pipeline (Nhóm 1)

**Môn:** AI trong hành động (AICB-P1)  
**Chủ đề:** Full RAG Pipeline — Indexing → Retrieval → Generation → Evaluation  
**Ngày thực hiện:** 13/04/2026  

---

## 1. Giới thiệu hệ thống

Nhóm xây dựng **trợ lý nội bộ cho bộ phận CS + IT Helpdesk**, có khả năng trả lời các câu hỏi về chính sách công ty, SLA ticket, quy trình cấp quyền hệ thống và FAQ kỹ thuật — dựa trên 5 tài liệu nội bộ thực tế.

**Hệ thống phải trả lời được các câu hỏi như:**
- "SLA xử lý ticket P1 là bao lâu?" → Trả lời từ `sla_p1_2026.txt`
- "Ai phải phê duyệt để cấp quyền Level 3?" → Trả lời từ `access_control_sop.txt`
- "ERR-403-AUTH là lỗi gì?" → **Abstain**: không có trong tài liệu, không bịa đặt

---

## 2. Phân công vai trò

| Thành viên | Vai trò | Sprint phụ trách |
|-----------|---------|-----------------|
| Đào Quang Thắng | Retrieval Owner | Sprint 1, 3 |
| Phạm Hoàng Kim Liên | Eval Owner & Documentation Owner | Sprint 4, docs |
| *(Tech Lead)* | Tech Lead | Sprint 1, 2 |

---

## 3. Kiến trúc tổng thể

```
[Raw Docs .txt × 5]
      ↓
[Sprint 1 — index.py]
  Preprocess (extract metadata) → Chunk (paragraph-based, 400 tokens/chunk, 80 overlap)
  → Embed (SentenceTransformers: paraphrase-multilingual-MiniLM-L12-v2)
  → Store (ChromaDB PersistentClient, cosine similarity)
      ↓
[ChromaDB Vector Store]
      ↓
[Sprint 2+3 — rag_answer.py]
  Query → Hybrid Retrieval (Dense + BM25/Sparse via RRF)
  → Rerank (optional Cross-Encoder) → Top-3 Context Block
  → Grounded Prompt → LLM (gpt-4o-mini, temperature=0)
  → Answer + Citations [1][2][3]
      ↓
[Sprint 4 — eval.py]
  Test Questions × 10 → run_scorecard() → LLM-as-Judge (4 metrics)
  → A/B Comparison (Baseline vs Variant) → Scorecard .md
```

---

## 4. Quyết định kỹ thuật chính

### Sprint 1 — Indexing

**Chunking Strategy:** Section-based + Paragraph fallback
- Ưu tiên cắt tại ranh giới `=== Section ===` (heading tự nhiên)
- Nếu section quá dài (>1600 ký tự), split tiếp theo `\n\n` (paragraph)
- Overlap 80 tokens để giữ ngữ cảnh qua ranh giới chunk

**Lý do không dùng fixed-size chunking thuần túy:**  
Tài liệu chính sách thường có cấu trúc theo "điều khoản" — cắt ngang giữa điều khoản làm mất ý nghĩa hoàn toàn. Ví dụ: cắt giữa "Điều 3: Ngoại lệ" sẽ khiến LLM không biết "ngoại lệ" áp dụng cho điều khoản nào.

**Metadata fields trên mỗi chunk:** `source`, `section`, `department`, `effective_date`, `access`

**Embedding model:** `paraphrase-multilingual-MiniLM-L12-v2` (Sentence Transformers, local)  
→ Lý do: Hỗ trợ tốt tiếng Việt, không tốn API cost, embed offline

### Sprint 2 — Baseline RAG

**Retrieval:** Dense search (ChromaDB, cosine similarity), `top_k=10`  
**Generation:** OpenAI `gpt-4o-mini`, `temperature=0`, `max_tokens=512`  
**Grounded Prompt:** 4 quy tắc cứng: Evidence-only, Abstain khi không đủ dữ liệu, Citation [n], Ngắn & nhất quán

### Sprint 3 — Variant: Hybrid Search

**Biến thay đổi duy nhất:** `retrieval_mode: dense → hybrid`

**Lý do chọn Hybrid (không phải Rerank hay Query Transform):**  
Phân tích tập test questions cho thấy 3/10 câu hỏi chứa keyword/alias kỹ thuật chính xác ("ERR-403-AUTH", "Approval Matrix", "P1"). Dense search xử lý tốt câu hỏi ngôn ngữ tự nhiên nhưng dễ bỏ sót exact keyword. BM25 bắt chính xác các chuỗi này. Hybrid (RRF) kết hợp ưu điểm của cả hai.

**Implement:** Reciprocal Rank Fusion với `dense_weight=0.6`, `sparse_weight=0.4`

---

## 5. Kết quả Evaluation — A/B Comparison

| Metric | Baseline (Dense) | Variant (Hybrid) | Delta |
|--------|-----------------|-----------------|-------|
| Faithfulness | 3.5/5 | 4.8/5 | **+1.3** |
| Answer Relevance | 3.8/5 | 4.7/5 | **+0.9** |
| Context Recall | 3.0/5 | 4.5/5 | **+1.5** |
| Completeness | 3.2/5 | 4.4/5 | **+1.2** |

**Câu hỏi Variant cải thiện nhiều nhất:**
- **q07** (Approval Matrix — alias cũ): Baseline Context Recall = 0 (không tìm được), Variant = 5 (tìm được nhờ BM25 khớp "approval" và "access-control")
- **q09** (ERR-403-AUTH — abstain): Baseline đôi khi trả về thông tin mơ hồ, Variant abstain đúng hơn vì BM25 xác nhận không có exact match → context block yếu → LLM kích hoạt abstain

**Câu hỏi cả hai đều tốt:** q01, q02, q05 (câu dễ, single-document, từ ngữ rõ ràng)

**Kết luận:** Variant Hybrid vượt trội Baseline **ở tất cả 4 metrics**. Cải thiện lớn nhất ở **Context Recall** (+1.5) — xác nhận giả thuyết rằng Dense search bỏ sót keyword/alias kỹ thuật là nguyên nhân chính của việc pipeline trả lời sai.

---

## 6. Debug Log (Error Tree)

Trong quá trình lab, nhóm gặp và xử lý:

| Vấn đề | Triệu chứng | Nguyên nhân | Cách fix |
|--------|-------------|-------------|---------|
| q07 baseline sai | Context Recall = 0 | Dense không match "Approval Matrix" với "Access Control SOP" | Chuyển sang Hybrid, BM25 bắt được keyword |
| LLM-as-Judge crash | `json.JSONDecodeError` | LLM trả về JSON kèm markdown blockquote | Thêm `.strip("\`").strip("json")` khi parse |
| Chunk cắt giữa điều khoản | `list_chunks()` thấy chunk bắt đầu ở giữa câu | Fixed-size cut không biết ranh giới | Dùng `\n\n` (paragraph boundary) |

---

## 7. Nhìn lại và hướng phát triển

**Điểm mạnh của pipeline hiện tại:**
- Abstain mechanism hoạt động tốt với `temperature=0` và grounded prompt
- Hybrid search giải quyết được cả câu hỏi ngôn ngữ tự nhiên lẫn keyword kỹ thuật

**Điểm cần cải tiến (nếu có thêm thời gian):**
1. **Cross-Encoder Reranker** (ms-marco-MiniLM-L-6-v2): Lọc thêm 1 lần nữa từ top-15 về top-3 với độ chính xác cao hơn, đặc biệt hữu ích khi corpus lớn hơn
2. **Adaptive RRF weights**: Tự động tăng `sparse_weight` khi query có ký tự đặc biệt (mã lỗi dạng `ERR-xxx`, `P1`)
3. **Freshness filter**: Sử dụng metadata `effective_date` để loại bỏ chunk từ tài liệu cũ khi có câu hỏi về version mới nhất
