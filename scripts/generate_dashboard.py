from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "data" / "logs.jsonl"
CONFIG_PATH = ROOT / "config" / "dashboard.yaml"
OUTPUT_PATH = ROOT / "submission" / "evidence" / "11-dashboard-runtime.html"


def percentile(values: list[float], percent: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(percent / 100 * len(ordered)) - 1))
    return ordered[index]


def load_records() -> list[dict]:
    records: list[dict] = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        timestamp = row.get("ts")
        if timestamp:
            row["_timestamp"] = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        records.append(row)
    return records


def render_panel(title: str, unit: str, value: str, detail: str, threshold: str, ok: bool) -> str:
    status = "WITHIN THRESHOLD" if ok else "THRESHOLD BREACHED"
    status_class = "ok" if ok else "bad"
    return f"""
    <section class="panel">
      <div class="panel-head"><h2>{title}</h2><span class="unit">{unit}</span></div>
      <div class="value">{value}</div>
      <div class="detail">{detail}</div>
      <div class="threshold {status_class}">{status}: {threshold}</div>
    </section>
    """


def main() -> None:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))["dashboard"]
    records = load_records()
    if not records:
        raise SystemExit("No records found in data/logs.jsonl")

    end = max(row["_timestamp"] for row in records if "_timestamp" in row)
    start = end - timedelta(minutes=config["time_range_minutes"])
    window = [row for row in records if row.get("_timestamp", datetime.min.replace(tzinfo=timezone.utc)) >= start]
    requests = [row for row in window if row.get("event") == "request_received"]
    responses = [row for row in window if row.get("event") == "response_sent"]
    failures = [row for row in window if row.get("event") == "request_failed"]

    latencies = [float(row.get("latency_ms", 0)) for row in responses]
    ttfts = [float(row.get("ttft_ms", 0)) for row in responses]
    p50, p95, p99 = (percentile(latencies, p) for p in (50, 95, 99))
    ttft_p95 = percentile(ttfts, 95)
    traffic_rate = len(requests) / max(1, config["time_range_minutes"])
    error_rate = len(failures) / max(1, len(requests)) * 100
    retrieval = [row for row in responses if row.get("tool_success") is not None]
    retrieval_success = sum(bool(row.get("tool_success")) for row in retrieval) / max(1, len(retrieval)) * 100
    cost = sum(float(row.get("cost_usd", 0)) for row in responses)
    tokens_in = sum(int(row.get("tokens_in", 0)) for row in responses)
    tokens_out = sum(int(row.get("tokens_out", 0)) for row in responses)
    quality_values = [float(row["quality_score"]) for row in responses if row.get("quality_score") is not None]
    quality = sum(quality_values) / max(1, len(quality_values))

    panels = [
        render_panel(
            "Latency percentiles and TTFT", "ms", f"P95 {p95:.0f}",
            f"P50 {p50:.0f} · P99 {p99:.0f} · TTFT P95 {ttft_p95:.0f}",
            "P95 ≤ 3000 ms", p95 <= 3000,
        ),
        render_panel(
            "Request traffic", "requests/min", f"{traffic_rate:.2f}",
            f"{len(requests)} requests in the selected window", "rate ≥ 1 request/min",
            traffic_rate >= 1,
        ),
        render_panel(
            "Error rate and retrieval success", "%", f"Errors {error_rate:.1f}%",
            f"Retrieval success {retrieval_success:.1f}% · {len(failures)} failed requests",
            "error rate ≤ 2% · retrieval ≥ 90%", error_rate <= 2 and retrieval_success >= 90,
        ),
        render_panel(
            "Cost over time", "USD", f"${cost:.4f}",
            f"Total across {len(responses)} responses", "total ≤ $2.50", cost <= 2.5,
        ),
        render_panel(
            "Input and output tokens", "tokens", f"{tokens_in + tokens_out:,}",
            f"Input {tokens_in:,} · Output {tokens_out:,}", "total ≤ 50,000",
            tokens_in + tokens_out <= 50000,
        ),
        render_panel(
            "Quality proxy", "score 0–1", f"{quality:.3f}",
            f"Mean across {len(quality_values)} scored responses", "mean ≥ 0.75", quality >= 0.75,
        ),
    ]

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{config['title']}</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;background:#07111f;color:#e8eef7;font-family:Segoe UI,Arial,sans-serif}}
.wrap{{max-width:1500px;margin:auto;padding:28px}} header{{display:flex;justify-content:space-between;align-items:end;margin-bottom:20px}}
h1{{font-size:28px;margin:0 0 8px}} .subtitle{{color:#98a9bf}} .badge{{background:#17263a;border:1px solid #2b405a;padding:10px 14px;border-radius:10px}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}} .panel{{background:#101d2e;border:1px solid #243850;border-radius:14px;padding:20px;min-height:190px}}
.panel-head{{display:flex;justify-content:space-between;gap:15px}} h2{{font-size:17px;margin:0;color:#c8d5e6}} .unit{{font-size:12px;color:#7f95ae}}
.value{{font-size:38px;font-weight:700;margin:28px 0 8px}} .detail{{color:#9fb1c7;min-height:38px}} .threshold{{margin-top:18px;padding-top:12px;border-top:1px solid #263b54;font-size:12px;font-weight:600}}
.ok{{color:#59d69b}} .bad{{color:#ff7285}} footer{{margin-top:18px;color:#7f95ae;font-size:12px}} @media(max-width:900px){{.grid{{grid-template-columns:1fr 1fr}}}}
</style></head><body><div class="wrap">
<header><div><h1>{config['title']}</h1><div class="subtitle">Runtime source: data/logs.jsonl · 6/6 required panels</div></div>
<div class="badge">Time range: Last {config['time_range_minutes']} minutes<br>Configured refresh interval: {config['refresh_seconds']} seconds<br>Snapshot window end: {end.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}</div></header>
<main class="grid">{''.join(panels)}</main>
<footer>Static runtime snapshot generated from {len(window)} structured log records. Re-run scripts/generate_dashboard.py to refresh. Thresholds follow config/dashboard.yaml.</footer>
</div></body></html>"""
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
