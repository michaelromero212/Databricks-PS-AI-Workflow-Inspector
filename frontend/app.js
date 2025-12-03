const API_BASE = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', () => {
    const jobSelect = document.getElementById('job-select');
    const scanBtn = document.getElementById('scan-btn');
    const statusIndicator = document.getElementById('status-indicator');
    const resultsArea = document.getElementById('results-area');
    const modelSelect = document.getElementById('model-select');

    // Fetch initial data
    fetchJobs();
    fetchStatus();
    fetchModels();

    // Refresh status every 30 seconds
    setInterval(fetchStatus, 30000);

    // Model selection event listener
    modelSelect.addEventListener('change', handleModelChange);

    // Job selection event listener
    jobSelect.addEventListener('change', () => {
        scanBtn.disabled = !jobSelect.value;
    });

    // Scan button click
    scanBtn.addEventListener('click', () => {
        if (jobSelect.value) {
            handleScan(jobSelect.value);
        }
    });

    async function fetchJobs() {
        try {
            const response = await fetch(`${API_BASE}/jobs`);
            const data = await response.json();

            // Clear existing options (except default)
            while (jobSelect.options.length > 1) {
                jobSelect.remove(1);
            }

            data.jobs.forEach(job => {
                const option = document.createElement('option');
                option.value = job.job_id;
                option.textContent = `${job.settings.name} (ID: ${job.job_id})`;
                jobSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error fetching jobs:', error);
            statusIndicator.textContent = 'Error connecting to backend. Is it running?';
            statusIndicator.classList.remove('hidden');
        }
    }

    async function fetchStatus() {
        try {
            const response = await fetch(`${API_BASE}/status`);
            if (response.ok) {
                const data = await response.json();

                // Update Databricks status
                const databricksStatus = document.getElementById('databricks-status');
                const databricksText = document.getElementById('databricks-status-text');

                if (data.databricks.connected) {
                    databricksStatus.className = 'status-badge connected';
                    databricksText.textContent = data.databricks.message;
                } else {
                    databricksStatus.className = 'status-badge disconnected';
                    databricksText.textContent = data.databricks.message;
                }

                // Update AI Model status
                const aiModelStatus = document.getElementById('ai-model-status');
                const aiModelText = document.getElementById('ai-model-status-text');

                if (data.ai_model.connected) {
                    aiModelStatus.className = 'status-badge connected';
                    aiModelText.textContent = `${data.ai_model.provider} (${data.ai_model.model})`;
                } else {
                    aiModelStatus.className = 'status-badge warning';
                    aiModelText.textContent = data.ai_model.message || 'Mock Mode';
                }
            }
        } catch (e) {
            console.error('Status fetch error:', e);
            document.getElementById('databricks-status').className = 'status-badge disconnected';
            document.getElementById('databricks-status-text').textContent = 'Backend Offline';
            document.getElementById('ai-model-status').className = 'status-badge disconnected';
            document.getElementById('ai-model-status-text').textContent = 'Backend Offline';
        }
    }

    async function handleScan() {
        const jobId = jobSelect.value;
        if (!jobId) return;

        // UI Updates
        scanBtn.disabled = true;
        statusIndicator.textContent = `Analyzing Job ${jobId}... This may take a minute.`;
        statusIndicator.classList.remove('hidden');
        resultsArea.classList.add('hidden');

        // Smooth scroll to status
        statusIndicator.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        try {
            const response = await fetch(`${API_BASE}/scan/${jobId}`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`Scan failed: ${response.statusText}`);
            }

            const data = await response.json();
            displayResults(data);

        } catch (error) {
            console.error('Scan error:', error);
            statusIndicator.textContent = `Error: ${error.message}`;
        } finally {
            scanBtn.disabled = false;
        }
    }

    function displayResults(data) {
        statusIndicator.classList.add('hidden');
        resultsArea.classList.remove('hidden');

        // Smooth scroll to results
        resultsArea.scrollIntoView({ behavior: 'smooth' });

        // Update Scores with animation
        animateScore('health-score', data.analysis.workflow_health_score);
        animateScore('notebook-score', data.analysis.notebook_score || 'N/A');
        animateScore('docs-score', data.analysis.docs_score);

        // Update Top Fixes
        const fixesList = document.getElementById('fixes-list');
        fixesList.innerHTML = '';
        data.analysis.top_fixes.forEach(fix => {
            const li = document.createElement('li');
            li.textContent = fix;
            fixesList.appendChild(li);
        });

        // Update Cluster Recs
        const clusterText = document.getElementById('cluster-text');
        const rec = data.analysis.cluster_recommendations;
        clusterText.innerHTML = `<strong>Recommendation:</strong> ${rec.size}<br><br>${rec.reasoning}`;

        // Detailed Issues
        const issuesContainer = document.getElementById('issues-container');
        issuesContainer.innerHTML = '';
        data.analysis.issues.forEach(issue => {
            const div = document.createElement('div');
            div.className = 'issue-item';
            div.innerHTML = `<span class="issue-severity-${issue.severity.toLowerCase()}">[${issue.severity}]</span> <strong>${issue.type}:</strong> ${issue.description}`;
            div.setAttribute('role', 'listitem');
            issuesContainer.appendChild(div);
        });

        // PDF Link
        const pdfBtn = document.getElementById('download-pdf-btn');
        pdfBtn.href = `${API_BASE}/report/${data.job_id}/pdf`;
    }

    function animateScore(elementId, targetValue) {
        const element = document.getElementById(elementId);
        if (typeof targetValue !== 'number') {
            element.textContent = targetValue;
            return;
        }

        let current = 0;
        const increment = Math.ceil(targetValue / 30);
        const timer = setInterval(() => {
            current += increment;
            if (current >= targetValue) {
                current = targetValue;
                clearInterval(timer);
            }
            element.textContent = current;
        }, 30);
    }

    async function fetchModels() {
        try {
            const response = await fetch(`${API_BASE}/models`);
            const data = await response.json();

            // Clear existing options
            modelSelect.innerHTML = '';

            // Populate dropdown with available models
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.key;
                option.textContent = model.name;

                // Select the current model
                if (model.key === data.current) {
                    option.selected = true;
                }

                modelSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error fetching models:', error);
            modelSelect.innerHTML = '<option value="">Error loading models</option>';
        }
    }

    async function handleModelChange() {
        const selectedModel = modelSelect.value;
        if (!selectedModel) return;

        try {
            const response = await fetch(`${API_BASE}/models/${selectedModel}`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                console.log(`Switched to model: ${data.model}`);
                // Refresh status to show new model
                fetchStatus();
            } else {
                console.error('Failed to switch model:', data.message);
                alert('Failed to switch model. Please try again.');
                // Reload models to reset selection
                fetchModels();
            }
        } catch (error) {
            console.error('Error switching model:', error);
            alert('Error switching model. Please try again.');
            fetchModels();
        }
    }
});
