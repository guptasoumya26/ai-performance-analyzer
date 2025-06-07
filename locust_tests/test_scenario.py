from locust import HttpUser, task, between, events
from statistics import mean
import json
from pathlib import Path
from datetime import datetime
import os

response_times = []
error_count = 0
request_count = 0

class WebsiteUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        self.endpoint = os.environ.get("LOCUST_ENDPOINT", "/delay/1")

    @task
    def load_test_endpoint(self):
        global response_times, error_count, request_count
        with self.client.get(self.endpoint, catch_response=True) as response:
            request_count += 1
            response_times.append(response.elapsed.total_seconds() * 1000)
            if response.status_code != 200:
                error_count += 1
                response.failure("Non-200 response")

@events.quitting.add_listener
def write_run_summary(environment, **kwargs):
    if not response_times:
        print("No successful requests made.")
        return

    avg_response = mean(response_times)
    p95 = sorted(response_times)[int(0.95 * len(response_times)) - 1]
    error_rate = (error_count / request_count) * 100 if request_count > 0 else 0

    run_data = {
        "run_id": datetime.now().strftime("%Y%m%d-%H%M%S"),
        "avg_response_time": round(avg_response, 2),
        "p95_response_time": round(p95, 2),
        "error_rate": round(error_rate, 2),
        "total_requests": request_count,
        "endpoint": os.environ.get("LOCUST_ENDPOINT", "/delay/1"),
        "timestamp": datetime.now().isoformat()
    }

    output_dir = Path(__file__).resolve().parent.parent / "data" / "runs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"run_{run_data['run_id']}.json"

    with open(output_path, "w") as f:
        json.dump(run_data, f, indent=2)

    print(f"\nTest results written to: {output_path}")
