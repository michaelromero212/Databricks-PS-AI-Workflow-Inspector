import os
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from dbx_client import DBXClient
from analyzer import WorkflowAnalyzer
from report_generator import ReportGenerator
from model_selector import ModelSelector

# Load environment variables
load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(title="Databricks PS AI Workflow Inspector")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Components
try:
    dbx_client = DBXClient()
    analyzer = WorkflowAnalyzer()
    report_gen = ReportGenerator()
    model_selector = ModelSelector()
except Exception as e:
    logger.error(f"Initialization Error: {e}")
    # Continue running so we can show errors in UI if possible, or just log it.
    # In production, might want to fail fast.

# --- API Endpoints ---

@app.get("/jobs")
async def list_jobs():
    """Lists available Databricks jobs."""
    jobs = dbx_client.list_jobs()
    
    # Filter to only show Inspector demo jobs
    # Include jobs that contain "Inspector" or "PS-AI-Workflow" in the name
    # Or match the specific demo job IDs
    demo_job_ids = ["576914796776653", "900088613589267", "392290392510064"]
    
    filtered_jobs = [
        job for job in jobs
        if (
            str(job.get("job_id")) in demo_job_ids or
            "Inspector" in job.get("settings", {}).get("name", "") or
            "PS-AI-Workflow" in job.get("settings", {}).get("name", "")
        )
    ]
    
    return {"jobs": filtered_jobs}

@app.get("/model-info")
async def get_model_info():
    """Returns the currently active LLM model."""
    return {"model": model_selector.get_active_model_name()}

@app.get("/models")
async def list_models():
    """Returns list of available AI models."""
    return {
        "models": model_selector.get_available_models(),
        "current": model_selector.current_model_key
    }

@app.post("/models/{model_key}")
async def select_model(model_key: str):
    """Select a different AI model."""
    success = model_selector.set_model(model_key)
    if success:
        return {"success": True, "model": model_selector.get_active_model_name()}
    else:
        return {"success": False, "message": "Invalid model key"}

@app.get("/status")
async def get_status():
    """Returns connection status for Databricks and AI Model."""
    status = {
        "databricks": {
            "connected": False,
            "message": "Not configured"
        },
        "ai_model": {
            "connected": False,
            "provider": model_selector.provider,
            "model": model_selector.model_name
        }
    }
    
    # Check Databricks connection
    try:
        jobs = dbx_client.list_jobs()
        
        # Apply same filtering as /jobs endpoint
        demo_job_ids = ["576914796776653", "900088613589267", "392290392510064"]
        filtered_jobs = [
            job for job in jobs
            if (
                str(job.get("job_id")) in demo_job_ids or
                "Inspector" in job.get("settings", {}).get("name", "") or
                "PS-AI-Workflow" in job.get("settings", {}).get("name", "")
            )
        ]
        
        status["databricks"]["connected"] = True
        status["databricks"]["message"] = f"Connected ({len(filtered_jobs)} jobs found)"
    except Exception as e:
        status["databricks"]["message"] = f"Error: {str(e)[:50]}"
    
    # Check AI Model
    if model_selector.provider == "huggingface":
        if model_selector.hf_token:
            status["ai_model"]["connected"] = True
            status["ai_model"]["message"] = model_selector.get_active_model_name()
        else:
            status["ai_model"]["connected"] = True  # Changed from False to True
            status["ai_model"]["message"] = f"Demo Mode - {model_selector.AVAILABLE_MODELS[model_selector.current_model_key]['display_name']}"
    elif model_selector.provider == "databricks":
        if model_selector.dbx_host and model_selector.dbx_token:
            status["ai_model"]["connected"] = True
        else:
            status["ai_model"]["message"] = "Not configured"
    
    return status

@app.post("/scan/{job_id}")
async def scan_job(job_id: str):
    """Triggers analysis for a specific job."""
    try:
        # Run analysis
        result = analyzer.analyze_job(job_id)
        
        if "error" in result:
             raise HTTPException(status_code=500, detail=result["error"])

        # Generate Reports
        md_path, pdf_path = report_gen.generate_report(result)
        
        # Add paths to result for frontend reference if needed
        result["report_paths"] = {
            "markdown": md_path,
            "pdf": pdf_path
        }
        
        return result
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report/{job_id}/pdf")
async def download_pdf(job_id: str):
    """Downloads the generated PDF report."""
    pdf_path = os.path.join("../outputs/reports", f"report_{job_id}.pdf")
    if os.path.exists(pdf_path):
        return FileResponse(pdf_path, media_type="application/pdf", filename=f"report_{job_id}.pdf")
    else:
        raise HTTPException(status_code=404, detail="Report not found. Please run scan first.")

# --- Static Files ---
# Serve frontend files from the root
# Note: We mount this last so API routes take precedence
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    logger.warning(f"Frontend directory not found at {frontend_path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
