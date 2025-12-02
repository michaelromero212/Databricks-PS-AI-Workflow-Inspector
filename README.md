# Databricks PS AI Workflow Inspector

A professional tool for scanning, analyzing, and documenting Databricks Jobs & Notebooks using the Databricks CLI, Python, and LLMs.

![Status](https://img.shields.io/badge/Status-Interview%20Ready-blue)
![Tech](https://img.shields.io/badge/Tech-FastAPI%20%7C%20React%20%7C%20Databricks%20CLI-orange)

## 📌 Project Goal
This tool allows Professional Services (PS) teams to quickly inspect a client's Databricks environment, analyze workflow health, and generate actionable reports using Generative AI.

## 🚀 Features
- **Job Inspection**: Lists all jobs via Databricks CLI.
- **Deep Scan**: Downloads notebook source code and configuration.
- **AI Analysis**: Uses LLMs (Databricks DBRX or Mistral-7B) to evaluate:
  - Notebook quality & Python best practices
  - SQL efficiency
  - Cluster sizing & cost optimization
  - Documentation completeness
- **Reporting**: Generates a comprehensive Markdown and PDF report.
- **UI**: Responsive, colorblind-safe web interface.

## 📂 Structure
```
databricks-ps-workflow-inspector/
├── backend/            # FastAPI application & Analysis logic
├── frontend/           # Vanilla JS/HTML/CSS UI
├── outputs/            # Generated reports and logs
└── start.sh            # One-click startup script
```

## 🛠️ Prerequisites
1. **Python 3.8+**
2. **Databricks CLI**: Installed and configured (`databricks configure`).
   - Ensure you can run `databricks jobs list` in your terminal.
3. **LLM Access** (Optional for demo, required for real analysis):
   - Set `HF_TOKEN` environment variable for HuggingFace (Mistral).
   - OR configure Databricks Serving in `backend/model_selector.py`.

## 🏁 Quick Start

1. **Clone & Navigate**
   ```bash
   cd databricks-ps-workflow-inspector
   ```

2. **Run the Application**
   ```bash
   ./start.sh
   ```
   This script will:
   - Create a virtual environment
   - Install dependencies
   - Start the FastAPI server

3. **Access the UI**
   Open your browser to [http://localhost:8000](http://localhost:8000)

## 🧪 How to Test (Interview Demo)
1. **Setup**:
   - Ensure `.env` is configured with your Databricks credentials.
   - Run `./start.sh` to launch the backend and frontend.

2. **Run the Demo**:
   - Open [http://localhost:8000](http://localhost:8000).
   - Select one of the pre-configured demo jobs:
     - **Inefficient Legacy ETL** (ID: 576914796776653) -> Expect Low Score
     - **Risky ML Pipeline** (ID: 392290392510064) -> Expect Medium Score
     - **Optimized ETL** (ID: 900088613589267) -> Expect High Score
   - Click **"Run Workflow Scan"**.
   - View the generated report and download the PDF.

## 🛡️ Security Note
- This project uses a `.env` file for credentials. **DO NOT commit this file to GitHub.**
- A `.gitignore` has been included to prevent accidental commits of secrets.

---
*Built for the Databricks Professional Services Team.*
