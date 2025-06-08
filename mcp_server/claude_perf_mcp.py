import asyncio
import sys
import json
from mcp.server.fastmcp import FastMCP, ToolCallContext, json_schema, handle_tool_call

# Define the tool class
class PerfInsightTools:
    @json_schema({
        "type": "object",
        "properties": {
            "beforeMetrics": {
                "type": "object",
                "description": "Performance metrics before change"
            },
            "afterMetrics": {
                "type": "object",
                "description": "Performance metrics after change"
            },
            "baseline_report": {
                "type": "string",
                "description": "Path to the baseline Locust run JSON file"
            },
            "test_report": {
                "type": "string",
                "description": "Path to the test Locust run JSON file"
            }
        },
        "anyOf": [
            {"required": ["beforeMetrics", "afterMetrics"]},
            {"required": ["baseline_report", "test_report"]}
        ]
    })
    @handle_tool_call("analyze_performance_diff", "Analyze performance difference between two metric snapshots")
    async def analyze_performance_diff(self, ctx: ToolCallContext, params: dict) -> dict:
        before = after = None
        if "baseline_report" in params and "test_report" in params:
            try:
                with open(params["baseline_report"], "r") as f:
                    before = json.load(f)
                with open(params["test_report"], "r") as f:
                    after = json.load(f)
            except Exception as e:
                raise ValueError(f"Failed to load input files: {e}")
        elif "beforeMetrics" in params and "afterMetrics" in params:
            before = params["beforeMetrics"]
            after = params["afterMetrics"]
        else:
            raise ValueError("You must provide either 'beforeMetrics' and 'afterMetrics' objects, or 'baseline_report' and 'test_report' file paths.")
        if not isinstance(before, dict) or not isinstance(after, dict):
            raise ValueError("'beforeMetrics' and 'afterMetrics' must be objects (dicts).")

        def safe_float(val):
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        def safe_divide(a, b):
            try:
                return round(((b - a) / a) * 100, 2)
            except Exception:
                return None

        results = {}
        for key in before:
            if key in after:
                a = safe_float(before[key])
                b = safe_float(after[key])
                change = safe_divide(a, b) if a is not None and b is not None else None
                results[key] = {
                    "before": before[key],
                    "after": after[key],
                    "change_percent": change
                }

        # Compose a human-readable analysis summary and diff_metrics for dashboard
        summary_lines = []
        diff_metrics = []
        for key, val in results.items():
            before_val = val.get("before")
            after_val = val.get("after")
            change = val.get("change_percent")
            status = ""
            if change is not None:
                if key in ["avg_response_time", "p95_response_time"]:
                    if change > 20:
                        status = "⚠️ Warning: Significant increase"
                    elif change < -20:
                        status = "✅ Stable: Significant improvement"
                    else:
                        status = "🟢 Stable"
                elif key == "error_rate":
                    if after_val > 5:
                        status = "🚨 Threat: High error rate"
                    elif after_val > 0:
                        status = "⚠️ Warning: Some errors"
                    else:
                        status = "🟢 Stable"
                elif key == "total_requests":
                    status = ""
                summary_lines.append(f"{key}: {before_val} → {after_val} ({change:+.2f}% change) {status}")
                diff_metrics.append({
                    "Metric": key,
                    "Before": before_val,
                    "After": after_val,
                    "% Change": change
                })
            else:
                summary_lines.append(f"{key}: {before_val} → {after_val} (no change computed)")
                diff_metrics.append({
                    "Metric": key,
                    "Before": before_val,
                    "After": after_val,
                    "% Change": None
                })
        conclusion = ""
        if any("Threat" in line for line in summary_lines):
            conclusion = "🚨 Conclusion: There is a performance threat that needs immediate attention."
        elif any("Warning" in line for line in summary_lines):
            conclusion = "⚠️ Conclusion: There are warnings. Please review the metrics."
        elif any("improvement" in line for line in summary_lines):
            conclusion = "✅ Conclusion: Performance has improved."
        else:
            conclusion = "🟢 Conclusion: System is stable."
        analysis = "\n".join(summary_lines) + "\n\n" + conclusion if summary_lines else "No significant differences found."
        return {
            "analysis": analysis,
            "diff_metrics": diff_metrics
        }

# Tool registration
async def main():
    mcp = FastMCP(PerfInsightTools)
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def stdin_reader():
        for line in sys.stdin:
            asyncio.run_coroutine_threadsafe(queue.put(line), loop)

    import threading
    threading.Thread(target=stdin_reader, daemon=True).start()

    while True:
        line = await queue.get()
        if not line:
            break
        try:
            request = json.loads(line)
            if request.get("method") == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "perfInsight", "version": "0.1.0"}
                    }
                }
            elif request.get("method") == "tools/list":
                tools = await mcp.list_tools()
                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {"tools": tools}
                }
            elif request.get("method") == "call_tool":
                params = request.get("params", {})
                call_id = params.get("call_id")
                tool_name = params.get("tool_name")
                input_data = params.get("input_data")
                result = await mcp.call_tool(call_id, tool_name, input_data)
                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": result
                }
            elif request.get("method") == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                if "baseline_report" in arguments and "test_report" in arguments:
                    try:
                        with open(arguments["baseline_report"], "r") as f:
                            before_metrics = json.load(f)
                        with open(arguments["test_report"], "r") as f:
                            after_metrics = json.load(f)
                        input_data = {
                            "beforeMetrics": before_metrics,
                            "afterMetrics": after_metrics
                        }
                    except Exception as e:
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "error": {"code": -32001, "message": f"Failed to load input files: {e}"}
                        }
                        sys.stdout.write(json.dumps(error_response) + "\n")
                        sys.stdout.flush()
                        break
                else:
                    input_data = arguments
                result = await mcp.call_tool(request["id"], tool_name, input_data)
                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": result
                }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
                break  # 🔥 Exit loop after one response
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {"code": -32601, "message": "Method not found"}
                }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32000, "message": str(e)}
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()
            break  # 🔥 Exit on failure too

if __name__ == "__main__":
    asyncio.run(main())
