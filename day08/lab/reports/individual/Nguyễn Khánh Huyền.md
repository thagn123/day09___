# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Khánh Huyền  
**Vai trò trong nhóm:** Tech Lead
**Ngày nộp:** [13.04.2026]

---

## 1. Phần việc đã thực hiện trong lab (100–150 từ)

Trong quá trình thực hiện lab, trọng tâm đóng góp nằm ở khâu rà soát mã nguồn, hợp nhất các thành phần đã được xây dựng bởi nhóm, và bảo đảm pipeline vận hành nhất quán từ đầu đến cuối. Cụ thể, công việc tập trung vào việc kiểm tra lại các file `index.py` và `rag_answer.py`, làm sạch một số hàm để thống nhất cách tổ chức mã, loại bỏ các đoạn log hoặc xử lý tạm thời không còn cần thiết, và xác minh tính liên thông giữa các bước indexing, retrieval và generation. Bên cạnh đó, quá trình hợp nhất mã cũng bao gồm việc kiểm tra đầu ra của từng module sau khi ghép nối, nhằm bảo đảm cấu trúc metadata, định dạng kết quả và luồng xử lý được duy trì đồng nhất. Vai trò này có ý nghĩa như một lớp kiểm soát kỹ thuật, giúp giảm sai lệch giữa các phần được phát triển riêng rẽ và hỗ trợ pipeline đạt trạng thái chạy được end-to-end.

---

## 2. Những nội dung được hiểu rõ hơn sau lab (100–150 từ)

Sau khi hoàn thành lab, có thể thấy rõ hơn rằng một hệ thống RAG không được quyết định chủ yếu bởi mô hình sinh ngôn ngữ, mà bởi chất lượng của toàn bộ pipeline trước bước generation. Cụ thể, chất lượng chunking và metadata có ảnh hưởng trực tiếp đến khả năng retrieval; nếu các đoạn văn bản bị cắt không hợp lý hoặc thông tin mô tả không nhất quán, mô hình sinh sẽ khó tạo ra câu trả lời đúng ngay cả khi context đã được cung cấp. Ngoài ra, sự khác biệt giữa dense retrieval và hybrid retrieval cũng trở nên rõ ràng hơn. Dense retrieval có ưu thế khi xử lý truy vấn mang tính ngữ nghĩa, trong khi hybrid retrieval cho thấy tiềm năng tốt hơn với các truy vấn chứa từ khóa đặc thù, alias hoặc tên gọi cũ. Lab này qua đó làm nổi bật bản chất của grounded prompting: câu trả lời chỉ đáng tin cậy khi được neo chặt vào bằng chứng đã retrieve.

---

## 3. Những điểm bất ngờ hoặc khó khăn phát sinh (100–150 từ)

Khó khăn lớn nhất không nằm ở việc thiết kế từng module riêng lẻ, mà xuất hiện trong giai đoạn tích hợp toàn bộ pipeline. Nhiều thành phần khi chạy độc lập cho kết quả hợp lý, nhưng khi ghép lại lại phát sinh những vấn đề nhỏ có ảnh hưởng đáng kể, chẳng hạn như sự không nhất quán trong cấu trúc đầu ra, các đoạn log cũ làm nhiễu quá trình kiểm tra, hoặc sự khác biệt về cách diễn giải score giữa dense retrieval và hybrid retrieval. Một điểm đáng chú ý khác là sự chênh lệch giữa kỳ vọng ban đầu và kết quả thực tế của variant hybrid. Về mặt ý tưởng, hybrid retrieval được kỳ vọng cải thiện chất lượng truy xuất; tuy nhiên, trong quá trình chạy thử, vấn đề threshold và cách chuẩn hóa score khiến hybrid ban đầu bị abstain quá mức. Điều này cho thấy trong các pipeline dạng RAG, khó khăn thường không nằm ở mô hình đơn lẻ mà ở việc chuẩn hóa giao diện và hành vi của toàn hệ thống.

---

## 4. Phân tích một câu hỏi trong scorecard (150–200 từ)

**Câu hỏi:** SLA xử lý ticket P1 là bao lâu?

**Phân tích:**

Đây là một trường hợp phù hợp để đánh giá hiệu quả của cả retrieval và generation. Ở baseline dense, hệ thống đã retrieve đúng đoạn quan trọng nhất từ tài liệu `support/sla-p1-2026.pdf`, cụ thể là phần quy định SLA theo mức độ ưu tiên. Từ context này, mô hình sinh đã tạo được câu trả lời ngắn gọn, đúng nội dung và có citation, bao gồm hai thông tin cốt lõi: phản hồi ban đầu trong 15 phút và thời gian xử lý trong 4 giờ. Điều đó cho thấy ở câu hỏi này, baseline dense đã hoạt động hiệu quả cả ở tầng truy xuất lẫn tầng sinh câu trả lời.

Khi chuyển sang variant hybrid, kết quả trả lời vẫn đúng và tiếp tục retrieve được đúng tài liệu liên quan. Tuy nhiên, mức cải thiện so với baseline không thật sự rõ rệt. Nguyên nhân chủ yếu không nằm ở indexing hay retrieval quality, mà ở chỗ baseline dense trên corpus hiện tại vốn đã đủ mạnh với loại câu hỏi mang cấu trúc rõ và có đáp án trực tiếp trong tài liệu. Trường hợp này cho thấy hybrid retrieval là một hướng mở rộng hợp lý, nhưng hiệu quả của nó cần được đánh giá trên những truy vấn khó hơn, đặc biệt là truy vấn phụ thuộc từ khóa, alias hoặc tên gọi cũ. :contentReference[oaicite:0]{index=0}

---

## 5. Nếu có thêm thời gian, các hướng cải tiến tiếp theo (50–100 từ)

Nếu có thêm thời gian, ưu tiên cải tiến sẽ là chuẩn hóa chặt chẽ hơn phần evaluation giữa baseline và variant, đặc biệt ở cách xử lý abstain và diễn giải retrieval score để bảo đảm log đầu ra phản ánh đúng hành vi hệ thống. Bên cạnh đó, một hướng khác là tiếp tục tinh chỉnh retrieval đối với các truy vấn ngoài phạm vi tài liệu hoặc các truy vấn chứa alias, do đây là nhóm câu hỏi cho thấy rõ nhất sự khác biệt giữa dense retrieval và hybrid retrieval. Cuối cùng, việc làm sạch mã nguồn và tách bạch rõ hơn phần core logic với phần debug cũng là một bước cần thiết để hỗ trợ bảo trì và mở rộng ở các bài sau.

---

