# Databricks notebook source
# MAGIC %md
# MAGIC # ML Training Pipeline
# MAGIC This notebook trains a model but lacks reproducibility and stability.

# COMMAND ----------

# ISSUE 1: Installing libraries at runtime without version pinning
# This can break if the library updates
%pip install scikit-learn tensorflow

# COMMAND ----------

import numpy as np
from sklearn.ensemble import RandomForestClassifier

# COMMAND ----------

# ISSUE 2: Non-deterministic behavior (No random seed)
# Every run produces different results
X = np.random.rand(1000, 10)
y = np.random.randint(0, 2, 1000)

clf = RandomForestClassifier(n_estimators=10)
clf.fit(X, y)

# COMMAND ----------

# ISSUE 3: Credentials in code (Security Risk)
# NEVER do this in production
aws_access_key = "AKIAIOSFODNN7EXAMPLE"
aws_secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# COMMAND ----------

# ISSUE 4: Single node dependency
# This code only runs on the driver and ignores the cluster workers
def train_model(data):
    # Heavy computation on driver
    return [x * 2 for x in data]

results = train_model(X.flatten())

# COMMAND ----------

print("Training complete.")
