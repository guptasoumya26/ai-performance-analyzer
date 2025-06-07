import json
from pathlib import Path
from datetime import datetime

def save_run_data(response_times, error_count, request_count, output_dir="data/runs"):
    if not response_times:
        return

    avg_latency = sum(response_times) / len(response_times)
    p95_latency = sorted(response_times)[int(0.95 * len(response_times)) - 1]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    data = {
        "timestamp": timestamp,
        "avg_latency_ms": round(avg_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
        "total_requests": request_count,
        "errors": error_count,
    }

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    with open(output_path / f"run_{timestamp}.json", "w") as f:
        json.dump(data, f, indent=2)
