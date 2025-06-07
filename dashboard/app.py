import streamlit as st
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import time
from datetime import datetime
import sys
import os
import threading
import queue

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.run_logger import save_run_data

st.set_page_config(page_title="Performance AI Analyzer", layout="wide")
st.title("📊 AI-Powered Performance Degradation Dashboard")

runs_path = Path(__file__).resolve().parent.parent / "data" / "runs"
runs_path.mkdir(parents=True, exist_ok=True)

def get_run_files():
    return sorted(runs_path.glob("*.json"), reverse=True)

def load_run_data(file):
    return json.loads(file.read_text())

st.sidebar.title("⚙️ Controls")
if st.sidebar.button("🗑️ Clear History"):
    for file in get_run_files():
        file.unlink()
    msg = st.success("✅ All runs deleted.")
    import time as pytime
    pytime.sleep(2)
    msg.empty()
if st.sidebar.button("🔄 Refresh Runs"):
    st.rerun()

left_col, mid_col = st.columns([1, 2])

with left_col:
    st.header("🚀 Run New Load Test")
    base_url = st.text_input("Base URL", "https://httpbin.org")
    endpoint = st.text_input("Endpoint", "/delay/1")
    num_users = st.slider("Number of Users", 1, 100, 10)
    spawn_rate = st.slider("Spawn Rate (users/sec)", 1, 50, 5)
    duration = st.slider("Test Duration (seconds)", 5, 60, 15)

    if st.button("Run Test"):
        log_placeholder = st.empty()
        progress_placeholder = st.empty()
        log_box_style = (
            "max-height: 300px; min-height: 200px; overflow-y: auto; "
            "background:#111; padding:8px; color:white; font-family:monospace; "
            "border: 1px solid #ccc; border-radius: 6px; margin-bottom: 8px;"
        )
        log_placeholder.markdown(
            f"<div style='{log_box_style}'><pre>Waiting for logs...</pre></div>", unsafe_allow_html=True
        )
        with st.spinner("Running test... please wait"):
            progress_bar = progress_placeholder.progress(0, text="0% completed")
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            command = [
                sys.executable, "-u", "-m", "locust",
                "-f", "locust_tests/test_scenario.py",
                "--headless", "-u", str(num_users), "-r", str(spawn_rate),
                "-t", f"{duration}s", "--host", base_url
            ]
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["LOCUST_ENDPOINT"] = endpoint
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True,
                env=env,
                creationflags=creationflags
            )

            q = queue.Queue()
            def enqueue_output(pipe, pipe_name):
                for line in iter(pipe.readline, ''):
                    q.put((pipe_name, line))
                pipe.close()

            t_stdout = threading.Thread(target=enqueue_output, args=(process.stdout, 'stdout'))
            t_stderr = threading.Thread(target=enqueue_output, args=(process.stderr, 'stderr'))
            t_stdout.daemon = True
            t_stderr.daemon = True
            t_stdout.start()
            t_stderr.start()

            stdout_lines = []
            start_time = time.time()
            while True:
                try:
                    pipe_name, line = q.get(timeout=0.1)
                except queue.Empty:
                    if process.poll() is not None:
                        break
                    elapsed = time.time() - start_time
                    if duration > 0:
                        progress = min(1.0, elapsed / duration)
                        percent = int(progress * 100)
                        progress_bar.progress(progress, text=f"{percent}% completed")
                    continue
                if line:
                    decoded = line.strip()
                    stdout_lines.append(decoded)
                    rendered = "\n".join(stdout_lines[-100:])
                    log_placeholder.markdown(
                        f"<div style='{log_box_style}'><pre>{rendered}</pre></div>",
                        unsafe_allow_html=True
                    )
                elapsed = time.time() - start_time
                if duration > 0:
                    progress = min(1.0, elapsed / duration)
                    percent = int(progress * 100)
                    progress_bar.progress(progress, text=f"{percent}% completed")
            process.wait()
            log_placeholder.empty()
            progress_bar.progress(1.0, text="100% completed")
            progress_placeholder.empty()

            if process.returncode == 0:
                st.success("✅ Load Test Completed Successfully!")
            else:
                st.error("❌ Load Test Failed. Check logs above.")

    st.header("📂 Select Runs for Comparison")
    run_files = get_run_files()
    if len(run_files) == 0:
        st.warning("⚠️ No test runs found. Please run a test.")
    elif len(run_files) == 1:
        st.info("ℹ️ 1 test run found. Please initiate one more run.")
    else:
        run1 = st.selectbox("Select Run 1", run_files, format_func=lambda x: x.stem)
        run2 = st.selectbox("Select Run 2", run_files, index=1, format_func=lambda x: x.stem)

with mid_col:
    st.subheader("📈 Performance Comparison Graph")
    if 'run1' not in locals() or 'run2' not in locals() or run1 == run2:
        st.markdown("<div style='color:#aaa; font-size:1.1rem; margin-bottom: 18px;'>Select runs to display the Graphical analysis.</div>", unsafe_allow_html=True)
    comparison_chart_placeholder = st.empty()
    st.subheader("🧠 AI Analysis Summary")
    if 'run1' not in locals() or 'run2' not in locals() or run1 == run2:
        st.markdown("<div style='color:#aaa; font-size:1.1rem; margin-bottom: 18px;'>Select runs to display the Summary.</div>", unsafe_allow_html=True)
    ai_analysis_placeholder = st.empty()

if 'run1' in locals() and 'run2' in locals() and run1 != run2:
    compare_col, ai_col = st.columns([1, 1])
    with compare_col:
        if st.button("Compare Performance"):
            data1 = load_run_data(run1)
            data2 = load_run_data(run2)
            metrics = [
                ("Avg Response Time (ms)", data1.get("avg_response_time", 0), data2.get("avg_response_time", 0)),
                ("95th Percentile (ms)", data1.get("p95_response_time", 0), data2.get("p95_response_time", 0)),
                ("Error Rate (%)", data1.get("error_rate", 0), data2.get("error_rate", 0)),
                ("Total Requests", data1.get("total_requests", 0), data2.get("total_requests", 0)),
            ]
            df = pd.DataFrame({
                "Metric": [m[0] for m in metrics],
                run1.stem: [m[1] for m in metrics],
                run2.stem: [m[2] for m in metrics],
            })
            df = df.set_index("Metric")
            comparison_chart_placeholder.bar_chart(df)
    with ai_col:
        if st.button("Claude Analysis"):
            import time as pytime
            try:
                from dashboard.mcp_runner import run_claude_analysis
                loading_placeholder = ai_analysis_placeholder.container()
                loading_msg = loading_placeholder.markdown("<div style='color:#aaa; font-size:1.1rem;'>⏳ Generating analysis...</div>", unsafe_allow_html=True)
                analysis_text, diff_metrics = run_claude_analysis(run1, run2)
                if diff_metrics:
                    filtered = [m for m in diff_metrics if isinstance(m.get('Before'), (int, float)) and isinstance(m.get('After'), (int, float))]
                    if filtered:
                        import plotly.graph_objects as go
                        diff_df = pd.DataFrame(filtered)
                        fig = go.Figure()
                        fig.add_trace(go.Bar(
                            x=diff_df['Metric'],
                            y=diff_df['Before'],
                            name='Before',
                            marker_color='rgba(255, 99, 132, 0.7)'
                        ))
                        fig.add_trace(go.Bar(
                            x=diff_df['Metric'],
                            y=diff_df['After'],
                            name='After',
                            marker_color='rgba(54, 162, 235, 0.7)'
                        ))
                        fig.add_trace(go.Bar(
                            x=diff_df['Metric'],
                            y=diff_df['% Change'],
                            name='% Change',
                            marker_color='rgba(100, 255, 100, 0.7)'
                        ))
                        fig.update_layout(
                            barmode='group',
                            title='Performance Metric Comparison',
                            xaxis_title='Metric',
                            yaxis_title='Value',
                            legend=dict(font=dict(size=16)),
                            xaxis=dict(tickfont=dict(size=18), titlefont=dict(size=20)),
                            yaxis=dict(tickfont=dict(size=18), titlefont=dict(size=20)),
                            margin=dict(l=40, r=40, t=60, b=120),
                            height=600,
                            font=dict(size=18)
                        )
                        comparison_chart_placeholder.plotly_chart(fig, use_container_width=True)
                pytime.sleep(3)
                loading_msg.empty()
                loading_placeholder.markdown(
                    f"""
                    <div style='background: #222; color: #fff; padding: 18px 20px; border-radius: 8px; font-size: 1.15rem; margin-bottom: 18px; line-height: 1.6;'>
                    <b>Claude Analysis:</b><br><br>{analysis_text.replace(chr(10), '<br>')}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            except Exception as e:
                ai_analysis_placeholder.error(f"Claude analysis failed: {e}")
