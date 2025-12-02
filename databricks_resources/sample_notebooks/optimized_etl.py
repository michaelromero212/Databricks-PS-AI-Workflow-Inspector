# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Standard ETL
# MAGIC This notebook demonstrates best practices for the Inspector to validate.

# COMMAND ----------

# BEST PRACTICE: Widgets for parameterization
dbutils.widgets.text("input_path", "/databricks-datasets/nyctaxi/sample/json/", "Input Path")
dbutils.widgets.text("output_table", "main.default.taxi_trips", "Output Table")

input_path = dbutils.widgets.get("input_path")
output_table = dbutils.widgets.get("output_table")

# COMMAND ----------

# BEST PRACTICE: Structured Streaming with Auto Loader
# Efficient, scalable ingestion
df = (spark.readStream
      .format("cloudFiles")
      .option("cloudFiles.format", "json")
      .option("cloudFiles.schemaLocation", "/tmp/schema/taxi")
      .load(input_path))

# COMMAND ----------

from pyspark.sql.functions import col, current_timestamp

# BEST PRACTICE: Vectorized transformations
df_transformed = (df
                  .select(
                      col("trip_distance").cast("double"),
                      col("fare_amount").cast("double"),
                      col("pickup_zip").alias("zip_code")
                  )
                  .withColumn("ingestion_time", current_timestamp())
                  .filter(col("trip_distance") > 0))

# COMMAND ----------

# BEST PRACTICE: Delta Lake with Merge Schema
(df_transformed.writeStream
 .format("delta")
 .option("checkpointLocation", "/tmp/checkpoints/taxi")
 .option("mergeSchema", "true")
 .trigger(availableNow=True)
 .table(output_table))
