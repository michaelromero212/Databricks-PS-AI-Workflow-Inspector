import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dbx_client import DBXClient

load_dotenv()

def check_runs():
    client = DBXClient()
    job_id = 576914796776653 # Inefficient ETL
    print(f"Fetching runs for job {job_id}...")
    runs = client.list_job_runs(job_id)
    
    if not runs:
        print("No runs found (or in demo mode).")
        # If no runs, we can't verify structure easily unless we mock it or trust docs.
        # But wait, the job might not have run yet.
        return

    print(f"Found {len(runs)} runs.")
    first_run = runs[0]
    print("First run keys:", first_run.keys())
    print("Duration:", first_run.get("execution_duration"))
    print("State:", first_run.get("state"))

if __name__ == "__main__":
    check_runs()
