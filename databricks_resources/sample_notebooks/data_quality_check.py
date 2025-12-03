# Databricks notebook source
# MAGIC %md
# MAGIC # Data Quality Validation Pipeline
# MAGIC This notebook performs data quality checks on customer data.
# MAGIC Demonstrates monitoring patterns with some room for improvement.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import *
from datetime import datetime, timedelta

# COMMAND ----------

# Load customer data
try:
    df = spark.table("default.customers")
except Exception as e:
    # ISSUE: Generic exception handling
    print(f"Error: {e}")
    df = spark.createDataFrame([], schema=StructType([]))

# COMMAND ----------

# Check for null values in critical columns
critical_columns = ["customer_id", "email", "created_date"]

for col in critical_columns:
    null_count = df.filter(F.col(col).isNull()).count()
    print(f"{col}: {null_count} nulls")

# COMMAND ----------

# Check for duplicate customer IDs
# GOOD: Using window functions for deduplication
from pyspark.sql.window import Window

window_spec = Window.partitionBy("customer_id").orderBy(F.desc("updated_at"))
df_deduped = df.withColumn("row_num", F.row_number().over(window_spec)) \
               .filter(F.col("row_num") == 1) \
               .drop("row_num")

duplicate_count = df.count() - df_deduped.count()
print(f"Found and removed {duplicate_count} duplicate records")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Check data freshness
# MAGIC SELECT 
# MAGIC   MAX(updated_at) as latest_update,
# MAGIC   DATEDIFF(NOW(), MAX(updated_at)) as days_old
# MAGIC FROM default.customers

# COMMAND ----------

# Validate email format
# GOOD: Using regex for validation
email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

df_validated = df_deduped.withColumn(
    "valid_email",
    F.col("email").rlike(email_pattern)
)

invalid_emails = df_validated.filter(F.col("valid_email") == False).count()
print(f"Invalid emails found: {invalid_emails}")

# COMMAND ----------

# ISSUE: Missing documentation on threshold values
quality_score = 100 - (invalid_emails / df.count() * 100)
print(f"Data Quality Score: {quality_score:.2f}%")

# COMMAND ----------

# Write quality metrics to monitoring table
# GOOD: Tracking metrics over time
metrics_df = spark.createDataFrame([{
    "check_date": datetime.now(),
    "total_records": df.count(),
    "duplicate_count": duplicate_count,
    "invalid_emails": invalid_emails,
    "quality_score": quality_score
}])

metrics_df.write.mode("append").saveAsTable("default.quality_metrics")
