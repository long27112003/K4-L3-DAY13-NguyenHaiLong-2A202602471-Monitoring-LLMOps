# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Hải Long
- **MSSV:** 2A202602471
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/long27112003/K4-L3-DAY13-NguyenHaiLong-2A202602471-Monitoring-LLMOps
- **Commit SHA cuối:** `8ac2f6e19dd359bda021ca4151013e35f6404452`
- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602471`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | [`evidence/01-pytest.txt`](evidence/01-pytest.txt) |
| Log validator | [`evidence/02-log-validator.png`](evidence/02-log-validator.png) |
| Dashboard validator | [`evidence/03-dashboard-validator.png`](evidence/03-dashboard-validator.png) |
| Structured log | [`evidence/04-structured-log.png`](evidence/04-structured-log.png) |
| PII redaction | [`evidence/05-pii-redaction.png`](evidence/05-pii-redaction.png) |
| Trace list | [`evidence/06-trace-list.png`](evidence/06-trace-list.png) — 38 root observations; nhóm trace mới có correlation ID hợp lệ |
| Trace waterfall | [`evidence/07-trace-waterfall.png`](evidence/07-trace-waterfall.png) — trace `9946a3fbb03845b15e1a6ba651a694fa` |
| Trace metadata | [`evidence/08a-trace-prompt-usage.png`](evidence/08a-trace-prompt-usage.png), [`evidence/08b-trace-correlation-metadata.png`](evidence/08b-trace-correlation-metadata.png) |
| Prompt versions | [`evidence/09-prompt-versions.png`](evidence/09-prompt-versions.png) — v1 `baseline`/`production`, v2 `candidate` |
| Prompt rollback | [`evidence/10a-prompt-promote.png`](evidence/10a-prompt-promote.png), [`evidence/10b-prompt-rollback.png`](evidence/10b-prompt-rollback.png) |
| Dashboard runtime | [`evidence/11-dashboard-overview.png`](evidence/11-dashboard-overview.png) — 6/6 panels, 60-minute range, units and thresholds |
| Incident metric | [`evidence/12-incident-metric.png`](evidence/12-incident-metric.png) — P95 2654 ms vượt ngưỡng 2000 ms |
| Incident log | [`evidence/13-incident-log.png`](evidence/13-incident-log.png) — `req-d8bb338d`, latency 2653 ms |
| Incident trace | [`evidence/14-incident-trace.png`](evidence/14-incident-trace.png) — retrieval 2.50s vs generation 0.15s |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Lần kiểm tra cuối phân tích 56 log records, 24 correlation ID duy nhất, không phát hiện PII leak. |
| `validate_dashboard.py` | HỢP LỆ (6/6 panel) | HỢP LỆ (6/6 panel) | Cấu hình đúng contract và dashboard runtime đã có đủ sáu panel. |
| `pytest` | 22 passed / 22 tests | 22 passed / 22 tests | Bao gồm kiểm tra child retriever/generation, prompt metadata, usage và cost. |
| Số traces hợp lệ | 0 | 38 root observations hiển thị | Ảnh chứng minh đúng project và có ít nhất 10 trace mới với correlation ID hợp lệ. |
| Số PII leak | 0 | 0 | Validator không phát hiện PII trong log hiện tại. |
| Latency P95 / TTFT P95 | 1140 ms / 50 ms | 2654 ms / 51 ms trong challenge | P95 vượt ngưỡng challenge 2000 ms nhưng TTFT ổn định, giúp khoanh vùng retrieval. |
| Retrieval success rate | 100% | 100% | 5/5 request challenge retrieval thành công nhưng chậm; dashboard runtime cũng hiển thị 100%. |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware nhận `x-request-id`; nếu thiếu thì sinh `req-<8-hex>`, bind vào `structlog.contextvars`, lưu trên `request.state` và trả lại qua response header.
- **Các metadata được ghi vào structured log:** `correlation_id`, `user_id_hash`, `session_id`, `feature`, `model`, `env`, event, timestamp, latency, TTFT, token, cost và quality.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` chạy trước `JsonlFileProcessor` và JSON renderer; raw user ID được băm, message/answer chỉ ghi bản preview đã scrub.
- **Cách kiểm chứng kết quả:** pytest kiểm tra middleware/PII; `validate_logs.py` kiểm tra schema, enrichment và PII runtime.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** ảnh `06-trace-list.png` hiển thị project `day13-k4-l3a-2A202602471`, tổng 38 root observations và nhóm ít nhất 10 trace mới lúc 15:47 có correlation ID hợp lệ; các ID được đối chiếu với workload/log cục bộ.
- **Cấu trúc root/retrieval/generation observations:** root `lab-agent-run`; child `retrieval` loại retriever chỉ ghi query preview đã scrub và số document; child `generation` ghi model, managed prompt link, token input/output, cost input/output và TTFT.
- **Cách nối trace với log:** cùng `correlation_id` được bind vào root metadata và metadata của cả hai child observation.
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** version 1, labels `baseline` và trạng thái production ban đầu.
- **Version/label candidate:** version 2, label `candidate`.
- **Trace ID của mỗi version:** v1/production `9946a3fbb03845b15e1a6ba651a694fa`; v2/production sau promote `744177e501f74a846290dd96eca1aceb` (correlation ID `req-386a82da`).
- **Cách promote và rollback `production`:** chuyển label `production` từ v1 sang v2, khởi động lại API để xóa prompt cache và chạy request kiểm chứng v2; sau đó gắn lại `production` cho v1. Hai ảnh `10a`/`10b` chứng minh trạng thái trước và sau rollback.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** latency/TTFT, traffic, errors/retrieval success, cost, tokens và quality; snapshot lấy cửa sổ 60 phút từ `data/logs.jsonl`, hiển thị interval cấu hình 30 giây, đầy đủ unit và threshold trong [`config/dashboard.yaml`](../config/dashboard.yaml). HTML được tính lại bằng [`scripts/generate_dashboard.py`](../scripts/generate_dashboard.py), không tự nhận là dashboard live.
- **SLO và lý do chọn:** 99.5% request phải có `response_sent` trong 3000 ms trên cửa sổ 28 ngày theo [`config/slo.yaml`](../config/slo.yaml). Baseline P95 khoảng 1140 ms nên 3000 ms đủ hấp thụ dao động bình thường nhưng vẫn bắt được chậm rõ với người dùng.
- **Cách tính error budget:** `100% - 99.5% = 0.5%`; trong 28 ngày tương đương `28 × 24 × 60 × 0.005 = 201.6 phút`, hoặc 5 request chậm/lỗi trên mỗi 1000 request.
- **Ba alert và runbook tương ứng:** P95 > 3000 ms trong 10 phút; error rate > 2% trong 5 phút; quality < 0.75 hoặc retrieval success < 90% trong 15 phút. Tất cả gửi `slack:#llmops-alerts`, có owner trong [`config/alert_rules.yaml`](../config/alert_rules.yaml) và hướng xử lý tại [`docs/alerts.md`](../docs/alerts.md).

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1` (cohort K4-L3A).
- **Khoảng thời gian điều tra:** 2026-09-29 16:16:17–16:16:30 ICT (09:16:17–09:16:30 UTC).
- **Triệu chứng từ metrics:** `latency_p95=2654 ms` và `latency_p99=2654 ms`, vượt ngưỡng challenge/SLO 2000 ms; `ttft_p95=51 ms`, error breakdown rỗng và request vẫn HTTP 200. CLI đo wall time khoảng 10.6–13.3 giây vì năm request concurrency bị blocking retrieval xử lý tuần tự trong async endpoint; latency riêng ghi trong log là khoảng 2.65 giây/request.
- **Log line và correlation ID liên quan:** chọn `req-d8bb338d`: `response_sent`, feature `monitoring`, `latency_ms=2653`, `ttft_ms=51`, `tool_name=retrieval`, `tool_success=true`. Bốn request còn lại cũng có latency 2652–2654 ms.
- **Trace ID và span gây ảnh hưởng:** trace `94b1a2a70add89967f5a54d6572bebd7`; root `lab-agent-run` 2.655s, child `retrieval` (`756595a0df4a5a36`) 2.502s, child `generation` (`a2083ee68d370eaa`) 0.153s. Timestamp trace khớp log của `req-d8bb338d`.
- **Root cause:** incident `rag_slow` thêm khoảng 2.5 giây vào hàm retrieval. Vì `retrieve()` dùng `time.sleep()` đồng bộ bên trong async request handler, concurrency còn làm các request chờ tuần tự, nên wall time nhìn từ load test tăng tới 10–13 giây.
- **Fix action:** tắt `rag_slow`; trong production, thay blocking retrieval bằng async I/O hoặc chạy tác vụ đồng bộ trong thread pool, đặt timeout/circuit breaker và fallback document để request không chờ kéo dài.
- **Preventive measure:** alert khi retrieval latency/P95 vượt ngưỡng trong 10 phút; thêm span-level latency dashboard, load test concurrency trong CI và test đảm bảo dependency retrieval có timeout/fallback.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** không capture raw prompt/output trong trace; chỉ lưu preview đã scrub, prompt metadata và managed prompt link để vẫn điều tra được mà giảm rủi ro PII.
- **Một lỗi/blocker đã gặp:** code ban đầu chỉ có root observation nên không thể phân biệt retrieval chậm với generation chậm.
- **Cách tìm nguyên nhân và xử lý:** đối chiếu yêu cầu SDK v4, thêm hai context observation cha-con và test recording client để kiểm tra loại observation, usage và cost.
- **Cách hiểu luồng Metrics → Logs → Traces:** metrics xác định loại triệu chứng và cửa sổ thời gian; log trong cửa sổ cung cấp request/correlation ID; trace cùng ID chỉ ra child span gây chậm hoặc lỗi.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** version giúp biết chính xác cấu hình tạo ra câu trả lời; token/cost phát hiện tăng chi phí; SLO biến kỳ vọng thành ngưỡng đo; rollback phục hồi nhanh khi candidate gây suy giảm.
- **Điều quan trọng nhất đã học:** observability có giá trị khi metric, log và trace dùng cùng định danh và có thể dẫn tới một hành động vận hành cụ thể.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** các phép đo đang dùng fake LLM và dashboard HTML local nên chưa đại diện tải production dài hạn; bước còn lại của CP4 là commit/push toàn bộ thay đổi, điền SHA cuối và nộp URL/SHA trên LMS.

### Source và kiểm thử đối chiếu

- Child observations và token/cost: [`app/agent.py`](../app/agent.py).
- Prompt resolution/version metadata: [`app/prompt_management.py`](../app/prompt_management.py).
- Correlation ID middleware: [`app/middleware.py`](../app/middleware.py).
- PII rules và scrubbing: [`app/pii.py`](../app/pii.py), [`app/logging_config.py`](../app/logging_config.py).
- Tests: [`tests/`](../tests/).

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
