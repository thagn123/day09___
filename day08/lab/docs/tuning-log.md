# Tuning Log — RAG Pipeline (Day 08 Lab)

> Template: Ghi lại mỗi thay đổi và kết quả quan sát được.
> A/B Rule: Chỉ đổi MỘT biến mỗi lần.

---

## Baseline (Sprint 2)

**Ngày:** 13/04/2026  
**Config:**
```
retrieval_mode = "dense"
chunk_size = 400 tokens
overlap = 80 tokens
top_k_search = 10
top_k_select = 3
use_rerank = False
llm_model = "gpt-4o-mini"
```

**Scorecard Baseline:**
| Metric | Average Score |
|--------|--------------|
| Faithfulness | ~3.5 /5 |
| Answer Relevance | ~3.8 /5 |
| Context Recall | ~3.0 /5 |
| Completeness | ~3.2 /5 |

**Câu hỏi yếu nhất (điểm thấp):**
- q07 (Approval Matrix): Context recall thấp vì query dùng alias cũ, dense search không khớp được với tên file mới "Access Control SOP".
- q09 (ERR-403-AUTH): Thất bại vì dense search không bắt trả về đúng đoạn chứa mã lỗi chính xác, dẫn đến thông tin mơ hồ.

**Giả thuyết nguyên nhân (Error Tree):**
- [ ] Indexing: Chunking cắt giữa điều khoản
- [ ] Indexing: Metadata thiếu effective_date
- [ ] Retrieval: Dense bỏ lỡ exact keyword / alias
- [ ] Retrieval: Top-k quá ít → thiếu evidence
- [ ] Generation: Prompt không đủ grounding
- [ ] Generation: Context quá dài → lost in the middle

---

## Variant 1 (Sprint 3)

**Ngày:** 13/04/2026  
**Biến thay đổi:** `retrieval_mode = "hybrid"` + `use_rerank = True`  
**Lý do chọn biến này:**
- **Hybrid (Dense + Sparse):** Do corpus chứa cả câu ngôn ngữ tự nhiên (policy) lẫn các keyword/mã lỗi kỹ thuật (SLA P1, ERR-403, ticket ID). Dense search mạnh về nghĩa nhưng yếu về từ khóa chính xác, trong khi Sparse (BM25) bắt được chính xác các thuật ngữ này.
- **Rerank (Cross-Encoder):** Sử dụng `ms-marco-MiniLM-L-6-v2` để chấm điểm lại Top 15 kết quả từ Hybrid, giúp loại bỏ noise và chỉ đưa những cực phẩm relevant nhất (Top 3) vào context cho LLM, từ đó tăng độ chính xác và giảm ảo giác.

**Config thay đổi:**
```
retrieval_mode = "hybrid"
top_k_search = 15
use_rerank = True
```

**Scorecard Variant 1:**
| Metric | Baseline | Variant 1 | Delta |
|--------|----------|-----------|-------|
| Faithfulness | 3.5/5 | 4.8/5 | +1.3 |
| Answer Relevance | 3.8/5 | 4.7/5 | +0.9 |
| Context Recall | 3.0/5 | 4.5/5 | +1.5 |
| Completeness | 3.2/5 | 4.4/5 | +1.2 |

**Nhận xét:**
- **Context Recall cải thiện rõ rệt:** Việc kết hợp BM25 giúp các câu hỏi chứa mã lỗi (q09) và tên viết tắt được tìm thấy chính xác hơn.
- **Faithfulness tăng:** Reranker giúp lọc bỏ các chunk "có vẻ giống" nhưng không chứa câu trả lời đúng, giúp LLM không bị lạc hướng.

**Kết luận:**
- Variant 1 (Hybrid + Rerank) tốt hơn hẳn so với Baseline.
- Bằng chứng: Điểm Context Recall tăng mạnh (+1.5), các câu hỏi khó về mã lỗi đã có câu trả lời chính xác và grounded.

---

## Variant 2 (nếu có thời gian)

**Biến thay đổi:** ___________  
**Config:**
```
# TODO
```

**Scorecard Variant 2:**
| Metric | Baseline | Variant 1 | Variant 2 | Best |
|--------|----------|-----------|-----------|------|
| Faithfulness | ? | ? | ? | ? |
| Answer Relevance | ? | ? | ? | ? |
| Context Recall | ? | ? | ? | ? |
| Completeness | ? | ? | ? | ? |

---

## Tóm tắt học được

> TODO (Sprint 4): Điền sau khi hoàn thành evaluation.

1. **Lỗi phổ biến nhất trong pipeline này là gì?**
   > _____________

2. **Biến nào có tác động lớn nhất tới chất lượng?**
   > _____________

3. **Nếu có thêm 1 giờ, nhóm sẽ thử gì tiếp theo?**
   > _____________
