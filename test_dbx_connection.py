import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dbx_client import DBXClient

# Load environment variables
load_dotenv()

def test_connection():
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    
    print(f"Testing connection to: {host}")
    print(f"Token present: {'Yes' if token else 'No'}")
    
    if not host or not token:
        print("❌ Missing DATABRICKS_HOST or DATABRICKS_TOKEN")
        return

    client = DBXClient()
    try:
        print("Attempting to list jobs...")
        jobs = client.list_jobs()
        print(f"✅ Connection successful! Found {len(jobs)} jobs.")
        for job in jobs:
            print(f" - Job ID: {job.get('job_id')} | Name: {job.get('settings', {}).get('name')}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_connection()
