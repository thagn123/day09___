# Tài liệu Chi tiết Mã nguồn RAG Pipeline

Tài liệu này giải thích chi tiết mục đích, đầu vào, đầu ra và logic xử lý của từng hàm trong các file code của dự án.

---

## 1. File: `index.py` (Hệ thống nạp dữ liệu - Indexing)

### `preprocess_document(raw_text, filepath)`
*   **Mục đích**: Làm sạch văn bản thô và bóc tách thông tin bổ trợ (Metadata).
*   **Logic**: 
    - Đọc các dòng đầu tiên của file để tìm các từ khóa như `Source:`, `Department:`, `Effective Date:`.
    - Loại bỏ phần header này khỏi nội dung chính.
    - Chuẩn hóa khoảng trắng (tối đa 2 dòng trống liên tiếp).
*   **Kết quả**: Trả về một Dict gồm văn bản đã làm sạch và Metadata tương ứng.

### `chunk_document(doc)`
*   **Mục đích**: Chia nhỏ tài liệu lớn thành các đoạn (chunks) có kích thước vừa phải.
*   **Logic**: 
    - Sử dụng Regex để tìm các tiêu đề mục dạng `=== Section ... ===`.
    - Chia tài liệu theo các đầu mục trước. Nếu một mục quá dài, nó sẽ gọi hàm `_split_by_size` để chia nhỏ tiếp.
*   **Kết quả**: Danh sách các chunks, mỗi chunk kèm theo metadata của tài liệu gốc và tên section đó.

### `_split_by_size(text, base_metadata, section)`
*   **Mục đích**: Hàm bổ trợ chia nhỏ văn bản theo đoạn văn (paragraph) và giữ tính liên kết (overlap).
*   **Logic**: 
    - Chia theo dấu `\n\n`.
    - Dồn các đoạn văn vào cho đến khi đạt `CHUNK_SIZE`.
    - Khi bắt đầu chunk mới, nó lấy một phần cuối của chunk trước (khoảng `CHUNK_OVERLAP`) dán vào đầu chunk sau để tránh mất ngữ cảnh ở ranh giới cắt.

### `get_embedding(text)`
*   **Mục đích**: Chuyển văn bản thành dãy số (vector).
*   **Logic**: Sử dụng mô hình `paraphrase-multilingual-MiniLM-L12-v2` từ thư viện `sentence_transformers`.
*   **Đặc điểm**: Chỉ tải model lên RAM một lần duy nhất (Lazy loading) để tiết kiệm thời gian.

### `build_index()`
*   **Mục đích**: Hàm trung tâm điều phối toàn bộ luồng Indexing.
*   **Logic**: Quét thư mục `data/docs/` -> Lần lượt Preprocess, Chunk, Embed -> Lưu tất cả vào **ChromaDB**.

---

## 2. File: `rag_answer.py` (Hệ thống Tra cứu & Sinh câu trả lời)

### `retrieve_dense(query, top_k)`
*   **Mục đích**: Tìm kiếm theo ý nghĩa (Semantic Search).
*   **Logic**: Chuyển câu hỏi của user thành vector, sau đó tính **Cosine Similarity** với các chunk trong ChromaDB để lấy ra những đoạn có "ý nghĩa" gần nhất.

### `retrieve_sparse(query, top_k)`
*   **Mục đích**: Tìm kiếm theo từ khóa chính xác (Keyword Tìm kiếm).
*   **Logic**: Sử dụng thuật toán **BM25**. Nó rất hữu ích khi user hỏi chính xác mã lỗi (ví dụ: "ERR-403") mà tìm kiếm ý nghĩa có thể bỏ qua.

### `retrieve_hybrid(query, top_k)`
*   **Mục đích**: Kết hợp sức mạnh của cả Dense và Sparse.
*   **Logic**: Gọi cả hai hàm tìm kiếm trên, sau đó dùng thuật toán **Reciprocal Rank Fusion (RRF)** để trộn kết quả. Những đoạn văn nào xuất hiện ở thứ hạng cao ở cả hai bên sẽ được ưu tiên đẩy lên đầu.

### `rerank(query, candidates)`
*   **Mục đích**: Lọc lại kết quả để lấy ra "cực phẩm".
*   **Logic**: Sử dụng mô hình **Cross-Encoder** (`ms-marco-MiniLM-L-6-v2`). Nó soi kỹ từng cặp (Câu hỏi - Đoạn văn) để chấm điểm mức độ liên quan tuyệt đối. Đây là bước "lọc tinh" sau khi đã tìm kiếm rộng.

### `rag_answer(query, ...)`
*   **Mục đích**: Trái tim của hệ thống.
*   **Luồng xử lý**: 
    1. Tra cứu (Retrieve) -> 2. Lọc lại (Rerank) -> 3. Đóng gói Context -> 4. Gọi LLM sinh câu trả lời.

---

## 3. File: `eval.py` (Hệ thống Đánh giá)

### `score_faithfulness(answer, chunks_used)`
*   **Mục đích**: Kiểm tra sự trung thực.
*   **Logic**: Yêu cầu LLM (đóng vai giám khảo) soi xem câu trả lời có "bốc phét" (Hallucination) thông tin gì mà không có trong dữ liệu đầu vào hay không.

### `score_context_recall(chunks_used, expected_sources)`
*   **Mục đích**: Kiểm tra khả năng tìm kiếm.
*   **Logic**: So sánh xem những tài liệu mà thầy giáo "kỳ vọng" (Expected Sources) có thực sự bị hệ thống của chúng ta tìm ra không.

### `run_scorecard(config)`
*   **Mục đích**: Chạy bài thi thử.
*   **Logic**: Lấy danh sách câu hỏi test, chạy qua pipeline RAG, sau đó gọi các hàm `score_*` để tổng kết điểm số trung bình cho toàn hệ thống.

---

## 4. File: `run_grading.py`

### `main()`
*   **Mục đích**: Xuất file nộp bài cuối cùng.
*   **Logic**: Chạy 10 câu hỏi "ẩn" (Grading Questions) với cấu hình tốt nhất (Hybrid + Rerank) và ghi kết quả vào file `grading_run.json`. Đây là file bạn dùng để nộp cho giảng viên.
