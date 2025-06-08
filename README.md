# 🚀 AI-Powered Performance Degradation Analyzer

This project provides an interactive dashboard for running, logging, visualizing, and AI-analyzing load test results for web endpoints. It is designed to help you detect, compare, and understand performance regressions in your web services using Locust and an LLM-powered analysis tool.

## ✨ Features

- 🏃 **Run Load Tests:** Easily configure and execute load tests on any HTTP endpoint using Locust.
- 📺 **Live Log Streaming:** View real-time logs and progress of running tests in the dashboard.
- 💾 **Result Storage:** Each test run is saved as a JSON file for later comparison.
- 📊 **Visual Comparison:** Select and compare two runs with clear bar charts of key metrics (latency, error rate, requests/sec, etc.).
- 🤖 **AI Analysis:** Get a natural language summary and risk assessment (Stable, ⚠️ Warning, 🔥 Threat, ✅ Conclusion) of performance differences using an LLM (Claude or similar) via a custom MCP server.
- 🕑 **History Management:** Clear or refresh run history from the sidebar.

## 🗂️ Project Structure

```
├── dashboard/
│   ├── app.py              # Streamlit dashboard UI and logic
│   ├── mcp_runner.py       # Helper to call the Claude MCP server for analysis
├── locust_tests/
│   └── test_scenario.py    # Locust test scenario (dynamic endpoint)
├── mcp_server/
│   ├── claude_perf_mcp.py  # JSON-RPC server for LLM-based analysis
│   └── mcp/                # Minimal MCP server framework
├── utils/
│   └── run_logger.py       # Utility for saving run data
├── data/
│   └── runs/               # Stores all run result JSON files
├── requirements.txt        # Python dependencies
├── .gitignore              # Git ignore rules
├── README.md               # Project documentation
```

## ⚡ Quick Start

1. 🛠️ **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

2. 🖥️ **Run the dashboard:**
   ```powershell
   streamlit run dashboard/app.py
   ```

3. 🏗️ **Run a test:**
   - Enter the Base URL and Endpoint.
   - Set users, spawn rate, and duration.
   - Click "Run Test" and watch live logs and progress.

4. 📈 **Compare runs:**
   - Select two runs from the dropdowns.
   - Click "Compare Performance" for a chart.
   - Click "Claude Analysis" for an AI-powered summary and risk assessment.

## 🧠 How It Works

- 🐍 **Locust** runs the load test and writes results to `data/runs/` as JSON.
- 🎛️ **Streamlit dashboard** lets you run tests, view logs, and compare results.
- 🤖 **Claude MCP server** (Python, JSON-RPC) compares two runs and returns a natural language summary with risk/conclusion labels.

## 🛠️ Customization

- ✏️ To change the test scenario, edit `locust_tests/test_scenario.py`.
- 🧩 To improve AI analysis, edit `mcp_server/claude_perf_mcp.py`.
- 📐 To add new metrics, update both the Locust scenario and the dashboard comparison logic.

## 📋 Requirements
- Python 3.8+
- See `requirements.txt` for all dependencies

## 📄 License
MIT License

---

🎉 **Enjoy fast, AI-powered performance analysis for your APIs!** 🚦
