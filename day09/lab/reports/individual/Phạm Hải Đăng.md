# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Phạm Hải Đăng  
**Vai trò trong nhóm:** Supervisor Owner
**Ngày nộp:** 14/04/2026
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

**Module/file tôi chịu trách nhiệm:**
- File chính: `graph.py`
- Functions tôi implement: Xây dựng cấu trúc `AgentState`, hàm `supervisor_node`, quản lý logic điều hướng (`route_decision`), placeholder cho `human_review_node`, và orchestrator chính `build_graph()` để quản lý luồng dữ liệu đi qua pipeline.

**Cách công việc của tôi kết nối với phần của thành viên khác:**
Phần luồng điều phối (Orchestrator) của tôi là xương sống cho toàn bộ hệ thống multi-agent. Tôi thiết lập từ điển `AgentState` để chuẩn hóa các tham số cho I/O contract giữa các worker. Node `supervisor_node` phân tách yêu cầu (query) từ user và dựa vào state flags để route task một cách chính xác tới `retrieval_worker` hoặc `policy_tool_worker` (những components do Worker Owner phát triển). Nếu tôi không lưu vết `route_reason` từ bước này, team Trace/Docs phân tích sẽ không thể biết vì sao hệ thống có quyết định như vậy.

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**
- Chỉnh sửa dòng code điều phối luồng xử lý và keyword if/else trong `graph.py` (tại function `supervisor_node` và hàm `run`).

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Tôi quyết định không sử dụng các phương pháp phân loại mô hình ngôn ngữ lớn (LLM classifier) để điều hướng trong `supervisor_node`, mà dùng keyword-based routing (route dựa theo tổ hợp từ khóa cứng).

**Lý do:** 
Tại bước phân luồng awal, chi phí thời gian thực thi (latency) và độ ổn định là thiết yếu hàng đầu. Gọi hàm LLM prompt thông thường tiêu tốn ít nhất 800 - 1000ms chỉ để trả về tên nhánh kết tiếp, gây bottleneck. Tôi chỉ định nhóm keyword-based routing theo mảng `policy_keywords` ("hoàn tiền", "level 3", v.v.) và `risk_keywords` ("khẩn cấp", "err-") là đủ để bao phủ 90% business case của hệ thống mock-up trợ lý nội bộ hiện tại. Rule-based bypass giúp rút ngắn latency của node đầu vào xuống mức < 10ms.

**Trade-off đã chấp nhận:**
Sự đánh đổi này là mất đi tính ngữ nghĩa học (semantic flexibility). Nếu request của user có ý hoàn tiền nhưng dùng từ lạ thay vì từ khóa "complain/refund/hoàn tiền", việc matching sẽ trượt và luồng routing bị bẻ sang default worker (`retrieval_worker`), có thể dẫn đến việc LLM synthesis sau cùng đưa ra đáp án không chuẩn sách chính sách đặc thù.

**Bằng chứng từ trace/code:**
```python
    policy_keywords = ["hoàn tiền", "refund", "flash sale", "license", "cấp quyền", "access", "level 3"]
    risk_keywords = ["emergency", "khẩn cấp", "2am", "không rõ", "err-"]

    if any(kw in task for kw in policy_keywords):
        route = "policy_tool_worker"
        route_reason = f"task contains policy/access keyword"
        needs_tool = True
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** Việc điều phối state thiếu context tài liệu khi `policy_tool_worker` cần gọi DB kiểm tra trước khi tổng hợp.

**Symptom (pipeline làm gì sai?):**
Ở giai đoạn code ban đầu, những query "Chính sách flash sale" route thẳng từ `supervisor_node` sang `policy_tool_worker` (nhánh độc lập). Kết quả policy_result gặp cảnh báo rỗng thông tin grounded, khiến `synthesis_worker` cạn evidence context và fail test sinh văn bản không đủ dữ liệu.

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**
Bản chất policy check vẫn cần căn cứ (text document) từ file text. Lỗi từ design pattern Routing bypass hoàn toàn `retrieval_worker` nếu rule được chọn là `policy_tool_worker`. State lúc chuyển qua thiếu key object list `retrieved_chunks`.

**Cách sửa:**
Trong ruột hàm `run` tại orchestrator `build_graph()`, ở nhánh `route == "policy_tool_worker"`, tôi thêm logic code dự phòng (fallback pattern): luôn kiểm tra tham số `retrieved_chunks`. Nếu là object List rỗng, Orchestrator sẽ ép graph tiếp tục gọi route qua `retrieval_worker_node` để vớt context document đầy đủ trước khi chốt hạ chuyển tiếp qua bước synthesis cuối.

**Bằng chứng trước/sau:**
```python
        elif route == "policy_tool_worker":
            state = policy_tool_worker_node(state)
            # Policy worker may need retrieval context first
            if not state["retrieved_chunks"]:
                state = retrieval_worker_node(state)
```

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Tôi thiết lập bộ chuẩn I/O dictionary object (`AgentState`) rất chi tiết, phủ luôn các param về metric thời gian chạy `latency_ms` và `route_reason`. Việc dựng flow routing bằng luồng Python thuần tốn ít công config phức tạp nhưng hiệu năng vẫn mượt qua các bài Unit Test độc lập.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Phần HITL (Human in The loop) mới chỉ là Node chặn bằng text in terminal chứ chưa được thiết lập cơ chế block asynchronus await human UI phê duyệt thật sự. Sự phụ thuộc if/else block còn khá cồng kềnh nếu có 50+ keywords trở lên.

**Nhóm phụ thuộc vào tôi ở đâu?**
Code `graph.py` của tôi là Entry point. Nếu tôi route hỏng, Worker Owner không có Input state để dev code logic, và Trace Docs không truy xuất ra được format `run_2026.json` để chạy grading.

**Phần tôi phụ thuộc vào thành viên khác:**
Tôi phụ thuộc vào Worker Owner đảm bảo format JSON Output sau mỗi module phải bám sát cấu trúc của AgentState contract, nếu họ trả về null hoặc thiếu Type field thì vòng lặp `run()` toàn bộ hệ thống sẽ báo lỗi KeyError.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ tiến hành di chuyển toàn bộ engine graph thủ công sang chuẩn cài đặt `LangGraph StateGraph` library thư viện cứng. Theo tôi thấy từ error trace, routing keyword đang bị hạn chế về coverage. Tôi dự định tạo thêm một local LLM node cực nhẹ dùng (ví dụ ollama - model mini) đảm nhận riêng tính năng intent classification giúp rẽ nhánh thông minh và uyển chuyển hơn, khắc phục hoàn toàn rủi ro bị trượt keyword khi query có mang ẩn dụ.
