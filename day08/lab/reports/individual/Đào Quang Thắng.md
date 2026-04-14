# Báo cáo cá nhân - [Tên Sinh Viên]

**Vai trò trong dự án:** Retrieval Owner

## 1. Đóng góp cụ thể trong Pipeline
*Trong dự án RAG Helpdesk, tôi phụ trách Sprint 1 (Xây dựng Index) và Sprint 3 (Tuning Tối Thiểu):*
- **Chiến lược Chunking & Metadata (Sprint 1):** Tôi đã viết kịch bản cắt nhỏ tài liệu (`_split_by_size`) ưu tiên dựa trên cấu trúc tự nhiên (dấu hiệu xuống dòng đoạn văn `\n\n`) thay vì cắt ngang từ một cách cơ học. Chunk size được thiết lập là 400 tokens cùng 80 tokens overlap. Tôi đảm bảo mọi chunk đều được gán metadata rất rõ ràng như `source`, `section` để LLM sau này có thể trích dẫn nguồn. Tôi cũng chọn model Vector Embedding là `paraphrase-multilingual-MiniLM-L12-v2` của thư viện `SentenceTransformers` dể thay thế cho OpenAI, điều này giúp nhóm tiết kiệm chi phí mà vẫn đảm bảo được ngữ nghĩa Tiếng Việt.
- **Tunning Chiến lược Tra cứu - Hybrid Search (Sprint 3):** Tôi chịu trách nhiệm cài đặt bản cập nhật thuật toán tra cứu (Retrieval) cải tiến. Thông qua đánh giá tài liệu nội bộ, tôi phát hiện có những mã quy trình hay Ticket rất chuyên ngành, Dense Vector thông thường gặp hạn chế do không chứa Key-word matching, cho nên tôi đã cài đặt giải pháp **Hybrid Search** bằng cách tính điểm tổng hợp giữa Dense Embedding (SentenceTransformers) kết hợp BM25 (Sparse) với công thức Reciprocal Rank Fusion (RRF). 

## 2. Phân tích 1 câu chấm điểm (Grading)
**Câu hỏi đã chọn:** [q07] *Approval Matrix để cấp quyền hệ thống là tài liệu nào?*
**Đánh giá tiến trình RAG của câu này:** 
- Giai đoạn Retrieval: Từ khóa *Approval Matrix* là tên cũ trong khi tài liệu chuẩn lại đang sử dụng tên "*Access Control SOP*". Ở cấu hình Dense Search mặc định từ đầu (Baseline), đôi lúc vector space bị nhiễu do điểm cosine bị chia lệch hướng. Bằng cách áp dụng **Hybrid Search**, các trọng số từ vựng (nhờ thuật toán BM25) cùng với vector hóa đều đồng thanh xếp hạng chunk chứa thông tin tốt nhất này vào Top 1 của Candidates.
- Giai đoạn Generation: Model LLM nhận được đúng Context Block hoàn hảo và thực hiện chính xác chỉ thị Prompt (Chỉ lấy thông tin được cung cấp - Grounded Answer) để trả lời đúng tên và mã của tài liệu.

## 3. Bài học / Rút kinh nghiệm
Qua quá trình triển khai dự án, tôi nhận ra được một bài học quan trọng: Kiến trúc RAG không chỉ phụ thuộc vào Model Sinh Ngôn Ngữ mạnh thế nào mà phần lớn "chết" ở luồng tra cứu dữ liệu (Retrieval). Nếu mình truyền thông tin sai cho model thì LLM sẽ luôn tự tin đưa ra kết quả sai lệch. Nhờ việc tự triển khai cơ chế **Reciprocal Rank Fusion (RRF)**, tôi thấy được sức mạnh cân bằng tỷ trọng của Hybrid Search: Nó vừa giữ lại được "sự linh hoạt" của tìm kiếm ngữ nghĩa, vừa giữ được sự chắc chắn/chính xác cao của tìm kiếm theo từ vựng (BM25), bù đắp lại các khuyết điểm của nhau.

## 4. Đề xuất cải tiến
Dựa vào bảng Scorecard thực tiễn ở file Variant, tôi nhận thấy có thể cân nhắc áp dụng các điểm sau:
1. **Áp dụng Cross-Encoder (Reranking):** Do hiện tại nhóm dùng trực tiếp Hybrid để sinh Top 3 chọn lọc. Việc bổ sung pipeline của thuật toán Reranking (Cross-Encoder) đánh giá chéo câu hỏi có thể giảm tải thời gian query của LLM hơn hẳn.
2. **Cấu hình Weight RRF linh hoạt:** Trong RRF, nếu query chứa dấu `-` như `ERR-403`, cấu hình có thể tự bắt Event trigger để tự động nâng trọng số Weight của Sparse (Keyword) lên 0.8 thay vì 0.4 cố định, giúp đẩy mạnh các kết quả Exact-match.
