import os
import subprocess
import json
import time
from dotenv import load_dotenv

load_dotenv()

WORKSPACE_ROOT = "/Shared/PS-AI-Workflow-Inspector"
LOCAL_NOTEBOOKS_DIR = "sample_notebooks" # Relative to this script

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"Stderr: {e.stderr}")
        return None

def upload_notebooks():
    print(f"Creating directory {WORKSPACE_ROOT}...")
    run_cmd(["databricks", "workspace", "mkdirs", WORKSPACE_ROOT])

    notebooks = [f for f in os.listdir(LOCAL_NOTEBOOKS_DIR) if f.endswith(".py")]
    
    uploaded_paths = {}
    
    for nb in notebooks:
        local_path = os.path.join(LOCAL_NOTEBOOKS_DIR, nb)
        remote_path = f"{WORKSPACE_ROOT}/{nb[:-3]}" # Remove .py extension
        
        print(f"Uploading {nb} to {remote_path}...")
        # Format SOURCE allows uploading .py files as notebooks
        # Added --language PYTHON to satisfy legacy CLI requirements
        run_cmd(["databricks", "workspace", "import", local_path, remote_path, "--format", "SOURCE", "--language", "PYTHON", "--overwrite"])
        uploaded_paths[nb] = remote_path
        
    return uploaded_paths

def create_job(name, notebook_path):
    print(f"Creating job: {name}...")
    
    # API 2.0 Format (Simpler, no 'tasks' array)
    job_config = {
        "name": name,
        "new_cluster": {
            "spark_version": "13.3.x-scala2.12",
            "node_type_id": "i3.xlarge",
            "num_workers": 1,
            "autotermination_minutes": 10
        },
        "notebook_task": {
            "notebook_path": notebook_path
        }
    }
    
    # Write config to temp file
    with open("temp_job_config.json", "w") as f:
        json.dump(job_config, f)
        
    result = run_cmd(["databricks", "jobs", "create", "--json-file", "temp_job_config.json"])
    
    if result:
        try:
            # Result might be just the ID or a JSON string depending on CLI version
            # Usually it returns JSON: {"job_id": 123}
            job_id = json.loads(result).get("job_id")
            print(f"Successfully created job {name} with ID: {job_id}")
            return job_id
        except json.JSONDecodeError:
             print(f"Job created but failed to parse ID from: {result}")
             return None
    else:
        print(f"Failed to create job {name}")
        return None

def main():
    print("--- Setting up Demo Environment ---")
    
    # 1. Upload Notebooks
    paths = upload_notebooks()
    
    if not paths:
        print("No notebooks uploaded. Exiting.")
        return

    # 2. Create Jobs
    jobs = []
    
    if "inefficient_etl.py" in paths:
        jobs.append(create_job("Inspector_Demo_Inefficient_ETL", paths["inefficient_etl.py"]))
        
    if "risky_ml_job.py" in paths:
        jobs.append(create_job("Inspector_Demo_Risky_ML", paths["risky_ml_job.py"]))
        
    if "optimized_etl.py" in paths:
        jobs.append(create_job("Inspector_Demo_Optimized_ETL", paths["optimized_etl.py"]))
        
    # Cleanup
    if os.path.exists("temp_job_config.json"):
        os.remove("temp_job_config.json")
        
    print("\n--- Setup Complete ---")
    print("You can now run the Inspector App and scan these jobs!")

if __name__ == "__main__":
    main()
