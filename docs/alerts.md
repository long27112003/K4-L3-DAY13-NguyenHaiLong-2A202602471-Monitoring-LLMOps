# Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: `high_user_visible_latency`
- Severity: critical
- Duration: 10 phút
- Kênh thông báo: `slack:#llmops-alerts`
- SLI/SLO liên quan: P95 latency và SLO request thành công trong 3000 ms.
- Điều kiện và thời gian duy trì: `latency_p95_ms > 3000` liên tục 10 phút.
- Ảnh hưởng tới người dùng: câu trả lời chậm, timeout hoặc người dùng gửi lại yêu cầu.
- Ba bước kiểm tra đầu tiên: (1) xác định cửa sổ tăng P95/TTFT; (2) lọc log chậm và lấy `correlation_id`; (3) mở trace tương ứng, so sánh thời gian retrieval và generation.
- Mitigation tạm thời: rollback prompt/model mới nếu generation tăng; giảm concurrency hoặc dùng fallback retrieval nếu retrieval tăng.
- Owner: `llm-platform`.

## Alert 2

- Tên: `elevated_request_error_rate`
- Severity: critical
- Duration: 5 phút
- Kênh thông báo: `slack:#llmops-alerts`
- SLI/SLO liên quan: error rate guardrail tối đa 2%.
- Điều kiện và thời gian duy trì: `error_rate_pct > 2` liên tục 5 phút.
- Ảnh hưởng tới người dùng: API trả lỗi và không nhận được câu trả lời.
- Ba bước kiểm tra đầu tiên: (1) phân nhóm `error_type`; (2) lấy log lỗi và `correlation_id`; (3) kiểm tra trace/span lỗi và trạng thái dependency.
- Mitigation tạm thời: chuyển sang dependency/fallback khỏe, giảm tải hoặc rollback thay đổi gần nhất.
- Owner: `api-oncall`.

## Alert 3

- Tên: `degraded_answer_quality`
- Severity: warning
- Duration: 15 phút
- Kênh thông báo: `slack:#llmops-alerts`
- SLI/SLO liên quan: quality trung bình tối thiểu 0.75 và retrieval success tối thiểu 90%.
- Điều kiện và thời gian duy trì: `quality_score_avg < 0.75` hoặc `retrieval_success_rate_pct < 90` liên tục 15 phút.
- Ảnh hưởng tới người dùng: câu trả lời ít liên quan, thiếu context hoặc phải hỏi lại.
- Ba bước kiểm tra đầu tiên: (1) đối chiếu quality/retrieval theo feature; (2) lấy request mẫu và correlation ID; (3) xem retrieval output count, prompt version và generation metadata trong trace.
- Mitigation tạm thời: rollback label `production` về prompt baseline và dùng fallback document đã kiểm chứng.
- Owner: `ai-quality`.
