# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Phạm Hoàng Kim Liên
**Vai trò trong nhóm:** MCP Owner 
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Trong dự án Lab Day 09, tôi chịu trách nhiệm chính về module **MCP (Model Context Protocol) Server** và hệ thống tương tác công cụ cho Agent. Cụ thể:
- **File chính:** `mcp_server.py` và `mcp_interactive.py`.
- **Functions tôi implement:** Tôi đã xây dựng các hàm `dispatch_tool`, `list_tools` để mô phỏng giao thức MCP Client-Server. Tôi trực tiếp cài đặt logic cho 4 công cụ (Tools): `search_kb` (kết nối với ChromaDB), `get_ticket_info` (tra cứu Jira mock), `check_access_permission` (kiểm tra luật SOP) và `create_ticket`.

**Cách công việc của tôi kết nối với phần của thành viên khác:**
Công việc của tôi là "trái tim" cung cấp khả năng hành động cho các Worker. Cụ thể, `policy_tool_worker` của thành viên khác gọi vào hàm `dispatch_tool` của tôi để thực thi các tác vụ ngoại vi mà LLM không tự làm được. Supervisor cũng dựa vào danh sách `TOOL_SCHEMAS` mà tôi định nghĩa để quyết định lộ trình điều hướng (`needs_tool`).

**Bằng chứng:**
- File `mcp_server.py` chứa định nghĩa `TOOL_SCHEMAS` và registry tools.
- Script `mcp_interactive.py` cho phép test độc lập các tool call.
- Commit logs cho thấy tôi đã cấu hình Virtual Environment và fix lỗi thiếu thư viện `chromadb` để `search_kb` có thể hoạt động thực tế.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Sử dụng **Keyword-based Routing kết hợp với MCP Discovery Schema** thay vì dùng LLM Classifer cho bước Supervisor định hướng ban đầu.

**Lý do:**
Ban đầu, nhóm cân nhắc dùng một LLM call (như GPT-4o-mini) trong `supervisor_node` để phân loại yêu cầu của user. Tuy nhiên, qua quá trình test với các câu hỏi về SLA và hoàn tiền, tôi nhận thấy keyword-based routing (với bộ từ khóa được tối ưu như `flash sale`, `license`, `p1`, `escalation`) mang lại tốc độ phản hồi cực nhanh (~10-20ms) so với LLM (~800ms-1200ms). Đồng thời, việc định nghĩa `inputSchema` chuẩn MCP giúp logic routing trở nên rõ ràng, dễ bảo trì hơn khi cần thêm tool mới.

**Trade-off đã chấp nhận:**
Keyword routing có thể bị sai nếu user dùng ngôn ngữ quá ẩn dụ hoặc không chứa từ khóa mục tiêu. Tuy nhiên, tôi đã chấp nhận trade-off này vì yêu cầu của bài Lab tập trung vào tính ổn định và tốc độ xử lý của pipeline Supervisor-Worker.

**Bằng chứng từ trace/code:**
Trong file `graph.py` (line 116-121), tôi đã gộp các bộ từ khóa từ cả bản local và remote để tối ưu độ phủ:
```python
policy_keywords = ["hoàn tiền", "refund", "flash sale", "license", "cấp quyền", "access", "level 3", "chính sách"]
retrieval_keywords = ["p1", "escalation", "sla", "ticket", "jira", "thời gian", "phản hồi", "quy trình", "sự cố", "đăng nhập", "remote", "thử việc", "probation"]
```
Kết quả trong trace JSON cho thấy `latency_ms` giảm đáng kể khi Supervisor không cần gọi API ngoài.

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** `ModuleNotFoundError: No module named 'chromadb'` và lỗi môi trường `externally-managed-environment`.

**Symptom:** 
Khi chạy `mcp_interactive.py` hoặc `graph.py`, hệ thống bị crash ngay lập tức khi gọi đến tool `search_kb`. Traceback cho thấy các thư viện quan trọng như `chromadb` và `sentence-transformers` chưa được cài đặt, mặc dù đã có file `requirements.txt`. Khi cố gắng cài đặt bằng `pip install`, macOS trả về lỗi bảo mật do Python do Homebrew quản lý không cho phép cài đặt global.

**Root cause:**
Môi trường Python trên máy Mac của tôi được cấu hình theo chuẩn PEP 668, yêu cầu phải dùng Virtual Environment để cài đặt package mới nhằm tránh làm hỏng Python hệ thống.

**Cách sửa:**
Tôi đã khởi tạo một môi trường ảo riêng biệt cho dự án:
1. `python3 -m venv .venv`
2. `source .venv/bin/activate`
3. Cài đặt lại toàn bộ dependencies: `pip install -r requirements.txt`

**Bằng chứng trước/sau:**
- **Trước khi sửa:** Tool `search_kb` trả về kết quả rỗng `{"chunks": [], "total_found": 0}` và in cảnh báo `WARNING: Using random embeddings`.
- **Sau khi sửa:** Tool `search_kb` đã load được model `all-MiniLM-L6-v2` và truy vấn thành công dữ liệu từ `chroma_db/`, trả về các thông tin chính xác về chính sách nghỉ ốm và SLA.

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Tôi đã hoàn thành tốt vai trò MCP Owner bằng việc xây dựng một hệ thống Tool Registry chuẩn mực, dễ mở rộng. Việc định nghĩa Schema chi tiết giúp Worker và Synthesis dễ dàng hiểu được format dữ liệu trả về mà không cần hard-code.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Tôi còn lúng túng khi xử lý các xung đột (Merge Conflict) lúc `git pull` từ repo chung của nhóm, dẫn đến mất thời gian cho việc rebase thủ công file `graph.py`.

**Nhóm phụ thuộc vào tôi ở đâu?**
Nếu module MCP của tôi không chạy, toàn bộ Agent sẽ "mù" thông tin về hệ thống bên ngoài (Jira, Database). Synthesis Worker sẽ không có context để trả lời các câu hỏi về Ticket hay Policy chuyên sâu.

**Phần tôi phụ thuộc vào thành viên khác:**
Tôi phụ thuộc vào Trace & Docs Owner để đảm bảo kết quả từ tool call của tôi được lưu lại chính xác trong file JSON artifacts, phục vụ cho việc chấm điểm (Scoring).

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ nâng cấp `mcp_server.py` thành một HTTP Server thực thụ bằng thư viện `fastmcp` thay vì dùng "mock class" như hiện tại. Trace của câu hỏi về ticket P1 cho thấy chúng ta đang import trực tiếp module, điều này vi phạm tính cô lập của microservices. Nếu dùng HTTP server, MCP server có thể chạy trên một container riêng, tăng tính linh hoạt và chuyên nghiệp cho hệ thống.

---
*Lưu file này với tên: `reports/individual/lien_pham.md`*  
