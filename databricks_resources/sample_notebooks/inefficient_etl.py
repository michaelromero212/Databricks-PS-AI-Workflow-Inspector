# Databricks notebook source
# MAGIC %md
# MAGIC # ETL Ingestion (Legacy)
# MAGIC This notebook ingests data but has several performance and best practice issues for the Inspector to find.

# COMMAND ----------

import pyspark.sql.functions as F
from pyspark.sql.types import *

# COMMAND ----------

# ISSUE 1: Hardcoded paths
input_path = "/dbfs/mnt/legacy/data/incoming.csv"
output_path = "/dbfs/mnt/legacy/data/processed/"

# COMMAND ----------

# ISSUE 2: Using pandas for big data (Driver OOM risk)
import pandas as pd

# We are reading a potentially large file into Pandas on the driver
pdf = pd.read_csv(input_path)

# COMMAND ----------

# ISSUE 3: Inefficient looping
# We are iterating through rows manually instead of using Spark vectorization
processed_rows = []
for index, row in pdf.iterrows():
    if row['status'] == 'active':
        processed_rows.append(row)

# COMMAND ----------

# ISSUE 4: Select * in SQL
# Creating a temp view to run inefficient SQL
spark.createDataFrame(pd.DataFrame(processed_rows)).createOrReplaceTempView("temp_data")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Selecting all columns is wasteful if we only need a few
# MAGIC SELECT * FROM temp_data WHERE value > 100 ORDER BY id

# COMMAND ----------

# ISSUE 5: No error handling or schema validation
# If the write fails, the job fails without cleanup
spark.table("temp_data").write.mode("overwrite").save(output_path)
