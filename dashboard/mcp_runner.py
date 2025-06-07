import sys
import subprocess
import json
from pathlib import Path

CLAUDE_MCP_PATH = Path(__file__).resolve().parent.parent / "mcp_server" / "claude_perf_mcp.py"

def call_mcp_tool(baseline_path, test_path):
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tools/call",
        "params": {
            "name": "analyze_performance_diff",
            "arguments": {
                "baseline_report": str(baseline_path),
                "test_report": str(test_path)
            }
        }
    }

    try:
        proc = subprocess.Popen(
            ["python", str(CLAUDE_MCP_PATH)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = proc.communicate(json.dumps(payload) + "\n", timeout=30)

        if proc.returncode != 0:
            raise RuntimeError(f"MCP error: {stderr.strip()}")

        for line in stdout.splitlines():
            try:
                result = json.loads(line)
                return result.get("result", result)
            except json.JSONDecodeError:
                continue

        raise ValueError("No valid JSON response from MCP.")
    except Exception as e:
        return {"error": f"Failed MCP call: {e}"}

def run_claude_analysis(run1_path, run2_path):
    result = call_mcp_tool(run1_path, run2_path)
    if 'error' in result:
        return result['error'], None
    analysis_text = result.get('analysis', 'No analysis returned.')
    diff_metrics = result.get('diff_metrics', [])
    return analysis_text, diff_metrics

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python mcp_runner.py <baseline_report> <test_report>")
        sys.exit(1)

    baseline_path = sys.argv[1]
    test_path = sys.argv[2]
    with open(baseline_path, 'r') as f1, open(test_path, 'r') as f2:
        baseline = json.load(f1)
        test = json.load(f2)
    result = call_mcp_tool(baseline, test)
    print(json.dumps(result, indent=2))
