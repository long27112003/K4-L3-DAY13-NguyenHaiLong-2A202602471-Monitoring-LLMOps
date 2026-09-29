# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Hải Long
- **MSSV:** 2A202602471
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/long27112003/K4-L3-DAY13-NguyenHaiLong-2A202602471-Monitoring-LLMOps
- **Commit SHA cuối:** Cập nhật sau khi commit bản hoàn thiện
- **Challenge ID:** TBD (đợi Lab Coach cấp ở CP3)
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602471`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | [`evidence/01-pytest.txt`](evidence/01-pytest.txt) |
| Log validator | [`evidence/02-log-validator.txt`](evidence/02-log-validator.txt) |
| Dashboard validator | [`evidence/03-dashboard-validator.txt`](evidence/03-dashboard-validator.txt) |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Schema, correlation ID, enrichment và PII đều pass trên 3 request runtime cục bộ. |
| `validate_dashboard.py` | HỢP LỆ (6/6 panel) | HỢP LỆ (6/6 panel) | Cấu hình dashboard đúng contract; ảnh runtime vẫn phải chụp sau workload. |
| `pytest` | 22 passed / 22 tests | 22 passed / 22 tests | Bao gồm kiểm tra child retriever/generation, prompt metadata, usage và cost. |
| Số traces hợp lệ | 0 | Chờ workload Langfuse | Code đã sẵn sàng; không ghi giả trace ID khi chưa upload thành công. |
| Số PII leak | 0 | 0 | Validator không phát hiện PII trong log hiện tại. |
| Latency P95 / TTFT P95 | 1140 ms / 50 ms | Đo lại sau workload | Ngưỡng SLO 3000 ms giữ khoảng đệm so với baseline. |
| Retrieval success rate | 100% | 100% trên workload cục bộ | 3/3 request retrieval thành công; cần đo lại trên workload Langfuse chính thức. |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware nhận `x-request-id`; nếu thiếu thì sinh `req-<8-hex>`, bind vào `structlog.contextvars`, lưu trên `request.state` và trả lại qua response header.
- **Các metadata được ghi vào structured log:** `correlation_id`, `user_id_hash`, `session_id`, `feature`, `model`, `env`, event, timestamp, latency, TTFT, token, cost và quality.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` chạy trước `JsonlFileProcessor` và JSON renderer; raw user ID được băm, message/answer chỉ ghi bản preview đã scrub.
- **Cách kiểm chứng kết quả:** pytest kiểm tra middleware/PII; `validate_logs.py` kiểm tra schema, enrichment và PII runtime.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** lọc project `day13-k4-l3a-2A202602471` theo session `cp2-baseline`/`cp2-candidate`, đối chiếu thời gian chạy workload và correlation ID trong log. Ảnh danh sách trace cần bổ sung sau khi workload upload thành công.
- **Cấu trúc root/retrieval/generation observations:** root `lab-agent-run`; child `retrieval` loại retriever chỉ ghi query preview đã scrub và số document; child `generation` ghi model, managed prompt link, token input/output, cost input/output và TTFT.
- **Cách nối trace với log:** cùng `correlation_id` được bind vào root metadata và metadata của cả hai child observation.
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** version 1, labels `baseline` và trạng thái production ban đầu.
- **Version/label candidate:** version 2, label `candidate`.
- **Trace ID của mỗi version:** Chờ chạy workload; không điền ID giả.
- **Cách promote và rollback `production`:** chuyển label `production` từ v1 sang v2, chạy một request kiểm chứng, sau đó gắn lại `production` cho v1 và chụp trạng thái trước/sau.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** latency/TTFT, traffic, errors/retrieval success, cost, tokens và quality; time range 60 phút, refresh 30 giây, đầy đủ unit và threshold trong `config/dashboard.yaml`.
- **SLO và lý do chọn:** 99.5% request phải có `response_sent` trong 3000 ms trên cửa sổ 28 ngày. Baseline P95 khoảng 1140 ms nên 3000 ms đủ hấp thụ dao động bình thường nhưng vẫn bắt được chậm rõ với người dùng.
- **Cách tính error budget:** `100% - 99.5% = 0.5%`; trong 28 ngày tương đương `28 × 24 × 60 × 0.005 = 201.6 phút`, hoặc 5 request chậm/lỗi trên mỗi 1000 request.
- **Ba alert và runbook tương ứng:** P95 > 3000 ms trong 10 phút; error rate > 2% trong 5 phút; quality < 0.75 hoặc retrieval success < 90% trong 15 phút. Tất cả gửi `slack:#llmops-alerts`, có owner và runbook tại `docs/alerts.md`.

## 7. Điều tra challenge

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** không capture raw prompt/output trong trace; chỉ lưu preview đã scrub, prompt metadata và managed prompt link để vẫn điều tra được mà giảm rủi ro PII.
- **Một lỗi/blocker đã gặp:** code ban đầu chỉ có root observation nên không thể phân biệt retrieval chậm với generation chậm.
- **Cách tìm nguyên nhân và xử lý:** đối chiếu yêu cầu SDK v4, thêm hai context observation cha-con và test recording client để kiểm tra loại observation, usage và cost.
- **Cách hiểu luồng Metrics → Logs → Traces:** metrics xác định loại triệu chứng và cửa sổ thời gian; log trong cửa sổ cung cấp request/correlation ID; trace cùng ID chỉ ra child span gây chậm hoặc lỗi.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** version giúp biết chính xác cấu hình tạo ra câu trả lời; token/cost phát hiện tăng chi phí; SLO biến kỳ vọng thành ngưỡng đo; rollback phục hồi nhanh khi candidate gây suy giảm.
- **Điều quan trọng nhất đã học:** observability có giá trị khi metric, log và trace dùng cùng định danh và có thể dẫn tới một hành động vận hành cụ thể.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** cần chạy workload không chứa dữ liệu định danh, chụp evidence Langfuse `06`–`10` và dashboard runtime `11`; CP3 chưa thực hiện vì chưa có challenge chính thức.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
