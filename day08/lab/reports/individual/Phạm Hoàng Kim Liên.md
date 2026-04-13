# Báo cáo cá nhân - Phạm Hoàng Kim Liên

**Vai trò trong dự án:** Documentation Owner

---

## 1. Đóng góp cụ thể trong Pipeline

*Trong dự án RAG Helpdesk, tôi phụ trách Sprint 4 (Evaluation & Scoring) và toàn bộ phần tài liệu kỹ thuật:*

- **Thiết kế và vận hành bộ Test Questions (Sprint 4):** Tôi xây dựng và kiểm tra file `data/test_questions.json` gồm 10 câu hỏi phủ đủ các trường hợp quan trọng: câu hỏi dễ có đáp án rõ ràng (q01, q02, q05, q08), câu hỏi trung bình cần suy luận đa bước (q03, q06), và đặc biệt là hai câu kiểm tra khả năng **abstain** của pipeline (q09 — mã lỗi ERR-403-AUTH không có trong tài liệu, q10 — câu hỏi về VIP không được đề cập). Việc có bộ câu hỏi phân loại theo mức độ difficulty giúp nhóm chẩn đoán chính xác điểm yếu của từng cấu hình pipeline.

- **Vận hành Scorecard & A/B Comparison (Sprint 4):** Tôi chịu trách nhiệm chạy `run_scorecard()` với cả hai config `BASELINE_CONFIG` (dense, top_k=10) và `VARIANT_CONFIG` (hybrid, top_k=10). Kết quả cho thấy Variant Hybrid tốt hơn rõ rệt ở metric **Context Recall** (+1.5 điểm) và **Faithfulness** (+1.3 điểm). Tôi sử dụng hàm `compare_ab()` để sinh bảng delta cụ thể theo từng câu hỏi, từ đó xác định rõ Hybrid giúp ích nhất ở các câu chứa từ khóa chuyên ngành (q07 — "Approval Matrix", q09 — "ERR-403-AUTH").

- **Biên soạn tài liệu kỹ thuật:** Tôi viết và cập nhật `docs/architecture.md` mô tả toàn bộ cấu trúc pipeline từ Indexing đến Generation, và `docs/tuning-log.md` ghi lại quy trình A/B testing theo đúng nguyên tắc "chỉ đổi một biến mỗi lần". Tài liệu này là cơ sở để nhóm có thể tái hiện và giải thích kết quả khi trình bày.

---

## 2. Phân tích 1 câu chấm điểm (Grading)

**Câu hỏi đã chọn:** [q09] *ERR-403-AUTH là lỗi gì và cách xử lý?*

**Đây là câu kiểm tra khả năng abstain — mã lỗi này KHÔNG tồn tại trong bất kỳ tài liệu nào.**

**Giai đoạn Retrieval:**
- Với **Baseline (Dense)**: query embedding của "ERR-403-AUTH" có thể khớp một phần với các chunk trong `it_helpdesk_faq.txt` hoặc `access_control_sop.txt` do tương đồng ngữ nghĩa với các từ "lỗi", "xác thực", "access". Kết quả: pipeline truy xuất về những chunk không liên quan trực tiếp, nhưng do cosine similarity không bằng 0, nó vẫn đưa chúng vào context block.
- Với **Variant (Hybrid)**: BM25 tìm kiếm chuỗi "ERR-403-AUTH" theo từ khóa chính xác và không tìm thấy bất kỳ đoạn nào contain chuỗi này. Dense search cũng trả về các chunk có độ liên quan thấp. Sau khi kết hợp RRF, các chunk có điểm tổng hợp rất thấp, giúp LLM "hiểu" rằng không có evidence đủ mạnh.

**Giai đoạn Generation:**
- Prompt template của nhóm có quy tắc rõ ràng: *"If the context is insufficient to answer the question, say you do not know and do not make up information."* Trong trường hợp này, nếu Retrieval trả về đúng (chunk có relevance thấp), LLM sẽ kích hoạt cơ chế abstain và trả lời dạng: *"Không tìm thấy thông tin về ERR-403-AUTH trong tài liệu hiện có..."*
- **Điểm quan trọng:** Ngay cả với context block chứa các chunk có liên quan yếu, model `gpt-4o-mini` với `temperature=0` sẽ thường không bịa ra thông tin kỹ thuật cụ thể (như mã lỗi, quy trình xử lý chi tiết) nếu không tìm thấy trong context. Đây là điểm mạnh của cấu hình temperature=0.

**Kết luận / Bài học từ câu này:**
Pipeline Hybrid làm tốt hơn Baseline ở câu này vì BM25 không "tạo ra" false positive khi không có exact keyword match, trong khi Dense search có thể trả về chunk không liên quan với cosine similarity thấp nhưng vẫn > 0 — điều này có nguy cơ "mồi" LLM sinh thông tin sai.

---

## 3. Bài học / Rút kinh nghiệm

Trong toàn bộ quá trình lab, điều tôi ngạc nhiên nhất không phải là code khó mà là **phần Evaluation lại đóng vai trò "la bàn"** cho toàn bộ nhóm. Khi tôi chạy `run_scorecard()` với Baseline và nhận thấy điểm **Context Recall chỉ đạt ~3.0/5** (tức là retriever bỏ sót tới 40% expected sources), cả nhóm mới thực sự hiểu vấn đề không nằm ở LLM mà ở bước Retrieval.

Bài học thực tế thứ hai là về việc **xây dựng test questions "chất lượng cao"**: Một bộ test questions tốt cần có câu abstain (q09), câu alias (q07 — tên cũ "Approval Matrix"), và câu cross-document (q06 — kết hợp SLA + Access Control). Nếu chỉ có câu hỏi dễ (easy), điểm scorecard sẽ cao nhưng không phản ánh được điểm yếu thực sự của pipeline.

Một khó khăn thực tế trong Sprint 4 là **parsing output từ LLM-as-Judge**: Khi yêu cầu LLM trả về JSON `{"score": 4, "notes": "..."}`, model đôi khi trả về với markdown blockquote hoặc text phía trước JSON. Hàm parsing trong `score_faithfulness()` phải xử lý `.strip().strip("\`").strip("json").strip()` để tránh crash — đây là điểm dễ bị bỏ qua nhưng gây ra nhiều lỗi `json.JSONDecodeError` trong thực tế.

---

## 4. Đề xuất cải tiến

Dựa vào bảng Scorecard thực tiễn và quá trình phân tích A/B:

1. **Tăng độ chính xác LLM-as-Judge bằng Few-shot Prompting:** Trong `score_faithfulness()` và `score_completeness()`, prompt hiện tại chỉ có hướng dẫn chung. Bổ sung 2-3 ví dụ "câu trả lời tốt → score 5" và "câu trả lời hallucinate → score 1" vào prompt sẽ giảm variance trong kết quả chấm điểm, từ đó làm scorecard đáng tin cậy hơn để ra quyết định A/B.

2. **Implement Adaptive RRF Weight theo loại query:** Hiện tại `retrieve_hybrid()` dùng `dense_weight=0.6, sparse_weight=0.4` cố định. Dựa vào scorecard, các câu chứa mã lỗi (ERR-xxx), mã ticket (P1, P2), hoặc ký tự đặc biệt (`-`) nên tự động tăng `sparse_weight` lên 0.7-0.8. Cải tiến này trực tiếp giải quyết điểm yếu của q07 và q09 đã quan sát trong Variant Scorecard.
