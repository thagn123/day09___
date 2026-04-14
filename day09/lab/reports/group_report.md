# Báo Cáo Nhóm — Lab Day 09: Multi-Agent Orchestration

**Tên nhóm:** Antigravity Team  
**Thành viên:**
| Tên | Vai trò | Email |
|-----|---------|-------|
| Phạm Hải Đăng | Supervisor Owner | dangph@example.com |
| Đào Quang Thắng | Worker Owner | thangdq@example.com |
| Nguyễn Khánh Huyền | MCP Owner | huyennk@example.com |
| Phạm Hoàng Kim Liên | Trace & Docs Owner | lienphk@example.com |

**Ngày nộp:** 2026-04-14  
**Repo:** Lecture-Day-08-09-10-main/day09/lab  
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Hướng dẫn nộp group report:**
> 
> - File này nộp tại: `reports/group_report.md`
> - Deadline: Được phép commit **sau 18:00** (xem SCORING.md)
> - Tập trung vào **quyết định kỹ thuật cấp nhóm** — không trùng lặp với individual reports
> - Phải có **bằng chứng từ code/trace** — không mô tả chung chung
> - Mỗi mục phải có ít nhất 1 ví dụ cụ thể từ code hoặc trace thực tế của nhóm

---

## 1. Kiến trúc nhóm đã xây dựng (150–200 từ)

> Mô tả ngắn gọn hệ thống nhóm: bao nhiêu workers, routing logic hoạt động thế nào,
> MCP tools nào được tích hợp. Dùng kết quả từ `docs/system_architecture.md`.

**Hệ thống tổng quan:**
Hệ thống sử dụng kiến trúc Supervisor-Worker gồm 4 Worker chuyên biệt: Retrieval (dense search), Policy Tool (kiểm tra chính sách + ngoại lệ), Synthesis (tổng hợp câu trả lời) và Human Review (cho các trường hợp rủi ro cao). Supervisor điều phối luồng dựa trên phân tích ý định và trích xuất từ khóa.

**Routing logic cốt lõi:**
Supervisor sử dụng Rule-based keyword matching kết hợp với Intent analysis. Nó phân loại query thành 3 nhóm: Thông tin chung (Retrieval), Chính sách/Quyền hạn (Policy Tool), và Sự cố khẩn cấp (Cần thêm cờ Risk_high).

**MCP tools đã tích hợp:**
> Liệt kê tools đã implement và 1 ví dụ trace có gọi MCP tool.

- `search_kb`: Công cụ tìm kiếm Knowledge Base tích hợp ChromaDB.
- `get_ticket_info`: Công cụ tra cứu trạng thái ticket từ Jira (mock).
- `check_access_permission`: Công cụ kiểm tra quyền hạn dựa trên role.

---

## 2. Quyết định kỹ thuật quan trọng nhất (200–250 từ)

> Chọn **1 quyết định thiết kế** mà nhóm thảo luận và đánh đổi nhiều nhất.
> Phải có: (a) vấn đề gặp phải, (b) các phương án cân nhắc, (c) lý do chọn phương án đã chọn.

**Quyết định:** Tách biệt Policy Logic ra khỏi Retrieval Worker.

**Bối cảnh vấn đề:**
Trong Day 08, LLM thường xuyên bỏ qua các ngoại lệ (như Flash Sale) nếu context quá dài. Chúng tôi cần một bước kiểm tra cứng (hard-check) hoặc phân tích tập trung vào policy.

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| Gộp chung Prompt | Nhanh, rẻ | Dễ hallucination, khó debug |
| Policy Worker riêng | Chính xác cao, dễ audit | Tăng latency, tốn thêm 1 LLM call |

**Phương án đã chọn và lý do:**
Chọn Policy Worker riêng vì độ chính xác về chính sách là quan trọng nhất cho IT Helpdesk service. Độ trễ 2-3s là chấp nhận được.

**Bằng chứng từ trace/code:**
Trong trace `run_20260414_105614.json`, query về "cấp quyền Level 3 khẩn cấp" đã kích hoạt `policy_tool_worker`, sau đó worker này gọi đồng thời 2 MCP tools: `search_kb` và `get_ticket_info`.

---

## 3. Kết quả grading questions (150–200 từ)

> Sau khi chạy pipeline với grading_questions.json (public lúc 17:00):
> - Nhóm đạt bao nhiêu điểm raw?
> - Câu nào pipeline xử lý tốt nhất?
> - Câu nào pipeline fail hoặc gặp khó khăn?

**Tổng điểm raw ước tính:** 84 / 100
*(Dựa trên việc check nhanh pipeline trả lời đúng 9/10 tiêu chí grading, con số thực tế có thể thay đổi tùy hội đồng chấm)*

**Câu pipeline xử lý tốt nhất:**
- ID: gq09 — Lý do tốt: Xử lý hoàn hảo câu hỏi multi-hop phức tạp nhất (SLA P1 kết hợp quy trình Emergency Access Level 2). Supervisor route đúng và Synthesis trích xuất chính xác điều kiện bypass từ 2 tài liệu khác nhau.

**Câu pipeline fail hoặc partial:**
- ID: gq08 — Fail ở đâu: Retrieval Worker không tìm thấy thông tin về chu kỳ đổi mật khẩu (mặc dù có trong tài liệu).
  Root cause: Do nội dung nằm ở cuối FAQ và bị đẩy xuống sau các chunk khác có độ tương đồng keyword thấp hơn.

**Câu gq07 (abstain):** Nhóm xử lý thế nào?
Xử lý tốt. Hệ thống nhận diện thông tin mức phạt tài chính không có trong tài liệu và trả về câu trả lời "Không đủ thông tin", tránh được lỗi hallucination.

**Câu gq09 (multi-hop khó nhất):** Trace ghi được 2 workers không? Kết quả thế nào?
Trace cho thấy Supervisor đã route sang `policy_tool_worker`, sau đó worker này tự động gọi `search_kb` (MCP) để lấy context. Kết quả rất chi tiết, bao quát đủ cả 3 kênh notification và điều kiện cho Level 2.

---

## 4. So sánh Day 08 vs Day 09 — Điều nhóm quan sát được (150–200 từ)

> Dựa vào `docs/single_vs_multi_comparison.md` — trích kết quả thực tế.

**Metric thay đổi rõ nhất (có số liệu):**
- **Độ trễ (Latency)**: Tăng từ ~3.2s lên 9.6s (+201%). Tuy nhiên, hệ thống Multi-Agent có khả năng xử lý các case phức tạp (P1, Flash Sale) mà Single-Agent thường trả lời sai hoặc bỏ sót context.
- **Routing Visibility**: Day 09 đạt 100% khả năng quan sát quá trình ra quyết định thông qua `route_reason`.

**Điều nhóm bất ngờ nhất khi chuyển từ single sang multi-agent:**
Khả năng tự động "phá vỡ" (break-down) các câu hỏi phức tạp của Supervisor. Ví dụ: Một câu hỏi vừa chứa yếu tố rủi ro vừa chứa yếu tố chính sách được Supervisor route qua Policy Worker, sau đó Worker này tự gọi tool tra cứu thông tin trước khi synthesis trả lời.

**Trường hợp multi-agent KHÔNG giúp ích hoặc làm chậm hệ thống:**
Với các câu hỏi FAQ đơn giản (ví dụ: "IT Helpdesk ở đâu?"), việc phải đi qua Supervisor và trích xuất embedding làm tăng độ trễ lên gấp nhiều lần mà không mang lại giá trị gia tăng về độ chính xác.

---

## 5. Phân công và đánh giá nhóm (100–150 từ)

> Đánh giá trung thực về quá trình làm việc nhóm.

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| ___ | ___________________ | ___ |
| ___ | ___________________ | ___ |
| ___ | ___________________ | ___ |
| ___ | ___________________ | ___ |

**Điều nhóm làm tốt:**

_________________

**Điều nhóm làm chưa tốt hoặc gặp vấn đề về phối hợp:**

_________________

**Nếu làm lại, nhóm sẽ thay đổi gì trong cách tổ chức?**

_________________

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì? (50–100 từ)

Nhóm sẽ tập trung vào 2 cải tiến:
1. **Parallel Execution**: Cho phép Supervisor gọi đồng thời Retrieval và Policy Worker thay vì tuần tự để giảm Avg Latency xuống dưới 5s.
2. **Context Persistence**: Cải thiện Synthesis Worker để ghi nhớ history của Supervisor trace, giúp câu trả lời cuối cùng có tính liền mạch và grounded hơn nữa.

---

*File này lưu tại: `reports/group_report.md`*  
*Commit sau 18:00 được phép theo SCORING.md*
