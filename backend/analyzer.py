import json
import logging
from dbx_client import DBXClient
from model_selector import ModelSelector

logger = logging.getLogger(__name__)

class WorkflowAnalyzer:
    def __init__(self):
        self.dbx = DBXClient()
        self.model = ModelSelector()

    def analyze_job(self, job_id):
        """Orchestrates the full analysis of a Databricks Job."""
        logger.info(f"Starting analysis for job {job_id}")
        
        # 1. Fetch Job Details
        try:
            job_details = self.dbx.get_job(job_id)
        except Exception as e:
            return {"error": str(e)}

        settings = job_details.get("settings", {})
        tasks = settings.get("tasks", [])
        
        # 2. Extract Code from Notebooks
        code_context = ""
        notebooks_analyzed = []

        for task in tasks:
            task_key = task.get("task_key")
            notebook_task = task.get("notebook_task")
            
            if notebook_task:
                path = notebook_task.get("notebook_path")
                logger.info(f"Fetching notebook for task {task_key}: {path}")
                
                source_code = self.dbx.export_notebook(path)
                if source_code:
                    code_context += f"\n--- NOTEBOOK: {path} (Task: {task_key}) ---\n"
                    code_context += source_code[:5000] # Truncate to avoid token limits for demo
                    notebooks_analyzed.append(path)
                else:
                    code_context += f"\n--- NOTEBOOK: {path} (Task: {task_key}) ---\n[Error retrieving source]\n"
            else:
                code_context += f"\n--- TASK: {task_key} (Type: {task.get('task_key')}) ---\n[Non-notebook task]\n"

        # 3. Construct Prompt
        prompt = self._build_prompt(settings, code_context)

        # 4. Get LLM Analysis
        logger.info("Sending context to LLM...")
        llm_response_str = self.model.generate_analysis(prompt)
        
        # 5. Parse Response
        try:
            # Attempt to extract JSON if the model wrapped it in text
            # This is a simple heuristic; robust implementations use structured decoding or regex
            start = llm_response_str.find('{')
            end = llm_response_str.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = llm_response_str[start:end]
                analysis_json = json.loads(json_str)
            else:
                # Fallback if no JSON found
                logger.warning("Could not parse JSON from LLM response.")
                analysis_json = self._get_fallback_analysis()
        except json.JSONDecodeError:
            logger.warning("JSON decode error on LLM response.")
            analysis_json = self._get_fallback_analysis()

        return {
            "job_id": job_id,
            "job_name": settings.get("name"),
            "notebooks": notebooks_analyzed,
            "analysis": analysis_json,
            "raw_llm_response": llm_response_str
        }

    def _build_prompt(self, job_settings, code_context):
        return f"""
You are an expert Databricks Solutions Architect. Analyze the following Databricks Job configuration and notebook code.

JOB CONFIGURATION:
{json.dumps(job_settings, indent=2)}

CODE CONTEXT:
{code_context}

INSTRUCTIONS:
Provide a comprehensive health report in JSON format with the following structure:
{{
  "workflow_health_score": <0-100 integer>,
  "issues": [
    {{"type": "<Category>", "severity": "<High/Medium/Low>", "description": "<text>"}}
  ],
  "cluster_recommendations": {{
    "size": "<Small/Medium/Large>",
    "reasoning": "<text>"
  }},
  "sql_rewrite_suggestions": ["<text>", ...],
  "python_code_improvements": ["<text>", ...],
  "docs_score": <0-100 integer>,
  "top_fixes": ["<text>", ...]
}}

Focus on:
1. Cluster sizing efficiency (is the driver too big? are workers needed?).
2. Python best practices (error handling, modularity).
3. SQL optimization.
4. Documentation completeness.
"""

    def _get_fallback_analysis(self):
        return {
            "workflow_health_score": 0,
            "issues": [{"type": "System", "severity": "High", "description": "Failed to generate AI analysis."}],
            "cluster_recommendations": {"size": "Unknown", "reasoning": "N/A"},
            "sql_rewrite_suggestions": [],
            "python_code_improvements": [],
            "docs_score": 0,
            "top_fixes": ["Check LLM connectivity"]
        }
