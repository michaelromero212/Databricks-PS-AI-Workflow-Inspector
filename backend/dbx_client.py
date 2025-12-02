import subprocess
import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DBXClient:
    def __init__(self):
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        if not self.demo_mode:
            try:
                self.check_cli_installed()
            except RuntimeError:
                logger.warning("Databricks CLI not found. Switching to DEMO MODE.")
                self.demo_mode = True

    def check_cli_installed(self):
        """Verifies that the Databricks CLI is installed and accessible."""
        try:
            subprocess.run(["databricks", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            logger.error("Databricks CLI not found. Please install it.")
            raise RuntimeError("Databricks CLI not found.")

    def list_jobs(self):
        """Lists all jobs in the workspace."""
        if self.demo_mode:
            return self._mock_jobs_list()

        try:
            # Using 'databricks jobs list --output JSON'
            result = subprocess.run(
                ["databricks", "jobs", "list", "--output", "JSON"],
                capture_output=True,
                text=True,
                check=True
            )
            data = json.loads(result.stdout)
            return data.get("jobs", [])
        except subprocess.CalledProcessError as e:
            logger.error(f"Error listing jobs: {e.stderr}")
            return []
        except json.JSONDecodeError:
            logger.error("Failed to parse jobs list JSON.")
            return []

    def get_job(self, job_id):
        """Retrieves details for a specific job."""
        if self.demo_mode:
            return self._mock_job_details(job_id)

        try:
            result = subprocess.run(
                ["databricks", "jobs", "get", "--job-id", str(job_id)],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting job {job_id}: {e.stderr}")
            raise

    def list_job_runs(self, job_id, limit=5):
        """Lists recent runs for a job."""
        if self.demo_mode:
            return []

        try:
            result = subprocess.run(
                ["databricks", "runs", "list", "--job-id", str(job_id), "--limit", str(limit), "--output", "JSON"],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout).get("runs", [])
        except subprocess.CalledProcessError as e:
            logger.error(f"Error listing runs for job {job_id}: {e.stderr}")
            return []

    def export_notebook(self, notebook_path):
        """Exports a notebook as source code."""
        if self.demo_mode:
            return self._mock_notebook_content(notebook_path)

        try:
            # databricks workspace export --format SOURCE <path>
            result = subprocess.run(
                ["databricks", "workspace", "export", "--format", "SOURCE", notebook_path],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Error exporting notebook {notebook_path}: {e.stderr}")
            return None

    def get_cluster_info(self, cluster_id):
        """Gets cluster configuration (if needed separately, though usually in job details)."""
        if self.demo_mode:
            return {}

        try:
            result = subprocess.run(
                ["databricks", "clusters", "get", "--cluster-id", cluster_id],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting cluster {cluster_id}: {e.stderr}")
            return None

    # --- MOCK DATA FOR DEMO ---
    def _mock_jobs_list(self):
        return [
            {"job_id": 1001, "settings": {"name": "ETL_Daily_Ingest_Demo"}},
            {"job_id": 1002, "settings": {"name": "ML_Training_Pipeline_Demo"}},
            {"job_id": 1003, "settings": {"name": "Legacy_SQL_Reports_Demo"}}
        ]

    def _mock_job_details(self, job_id):
        # Return different cluster configs based on job_id to show cost variation
        job_id_int = int(job_id)
        
        if job_id_int == 576914796776653:  # Inefficient ETL - Low score, small Serverless
            return {
                "job_id": job_id_int,
                "settings": {
                    "name": "ETL_Daily_Ingest_Demo (Inefficient)",
                    "tasks": [
                        {
                            "task_key": "ingest_data",
                            "notebook_task": {"notebook_path": "/Users/demo/ingest_notebook"}
                        }
                    ],
                    "environments": [{"environment_key": "default"}]  # Serverless
                }
            }
        elif job_id_int == 392290392510064:  # Risky ML - Medium score, medium cluster
            return {
                "job_id": job_id_int,
                "settings": {
                    "name": "ML_Training_Pipeline_Demo (Risky)",
                    "tasks": [
                        {
                            "task_key": "train_model",
                            "notebook_task": {"notebook_path": "/Users/demo/train_notebook"},
                            "new_cluster": {
                                "spark_version": "13.3.x-scala2.12",
                                "node_type_id": "m5.xlarge",
                                "num_workers": 4
                            }
                        }
                    ]
                }
            }
        elif job_id_int == 900088613589267:  # Optimized ETL - High score, large cluster
            return {
                "job_id": job_id_int,
                "settings": {
                    "name": "Optimized_ETL_Demo",
                    "job_clusters": [
                        {
                            "job_cluster_key": "large_cluster",
                            "new_cluster": {
                                "spark_version": "13.3.x-scala2.12",
                                "node_type_id": "i3.2xlarge",
                                "autoscale": {
                                    "min_workers": 4,
                                    "max_workers": 12
                                }
                            }
                        }
                    ],
                    "tasks": [
                        {
                            "task_key": "optimized_etl",
                            "notebook_task": {"notebook_path": "/Users/demo/optimized_notebook"},
                            "job_cluster_key": "large_cluster"
                        }
                    ]
                }
            }
        else:
            # Generic fallback
            return {
                "job_id": job_id_int,
                "settings": {
                    "name": f"Demo Job {job_id}",
                    "tasks": [
                        {
                            "task_key": "generic_task",
                            "notebook_task": {"notebook_path": "/Users/demo/generic_notebook"}
                        }
                    ],
                    "job_clusters": [
                        {
                            "job_cluster_key": "auto_scaling_cluster",
                            "new_cluster": {
                                "spark_version": "13.3.x-scala2.12",
                                "node_type_id": "i3.xlarge",
                                "num_workers": 8
                            }
                        }
                    ]
                }
            }

    def _mock_notebook_content(self, path):
        return """
# Databricks notebook source
import pyspark.sql.functions as F

# COMMAND ----------

# Ingest Data
df = spark.read.format("csv").load("/mnt/data/raw")

# COMMAND ----------

# Transformation (Inefficient)
# TODO: Fix this select *
df_clean = df.select("*").filter("id > 0")

# COMMAND ----------

df_clean.write.mode("overwrite").saveAsTable("clean_data")
"""
