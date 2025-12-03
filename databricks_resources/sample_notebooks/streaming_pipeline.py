# Databricks notebook source
# MAGIC %md
# MAGIC # Streaming Event Processing Pipeline
# MAGIC Real-time processing of clickstream events using Structured Streaming.
# MAGIC Demonstrates streaming best practices.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import *

# COMMAND ----------

# Define schema for incoming events
# GOOD: Explicit schema definition
event_schema = StructType([
    StructField("event_id", StringType(), False),
    StructField("user_id", StringType(), False),
    StructField("event_type", StringType(), False),
    StructField("timestamp", TimestampType(), False),
    StructField("properties", MapType(StringType(), StringType()), True)
])

# COMMAND ----------

# Read from streaming source
# NOTE: Using Auto Loader for cloud files
stream_df = spark.readStream \
    .format("cloudFiles") \
    .option("cloudFiles.format", "json") \
    .option("cloudFiles.schemaLocation", "/mnt/checkpoints/events/schema") \
    .schema(event_schema) \
    .load("/mnt/raw/events/")

# COMMAND ----------

# Transform events
# GOOD: Using watermarking for late data handling
processed_stream = stream_df \
    .withWatermark("timestamp", "10 minutes") \
    .filter(F.col("event_type").isin(["click", "purchase", "view"])) \
    .withColumn("processing_time", F.current_timestamp()) \
    .withColumn("hour", F.hour(F.col("timestamp"))) \
    .withColumn("date", F.to_date(F.col("timestamp")))

# COMMAND ----------

# Aggregate clicks by hour
# GOOD: Using window aggregations
hourly_stats = processed_stream \
    .groupBy(
        F.window(F.col("timestamp"), "1 hour"),
        F.col("event_type")
    ) \
    .agg(
        F.count("*").alias("event_count"),
        F.countDistinct("user_id").alias("unique_users")
    )

# COMMAND ----------

# Write to Delta table with checkpointing
# GOOD: Using checkpoints for fault tolerance
query = processed_stream.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", "/mnt/checkpoints/events/raw") \
    .option("mergeSchema", "true") \
    .table("default.processed_events")

# COMMAND ----------

# Write aggregated stats
# GOOD: Separate stream for aggregations
stats_query = hourly_stats.writeStream \
    .format("delta") \
    .outputMode("complete") \
    .option("checkpointLocation", "/mnt/checkpoints/events/stats") \
    .table("default.event_hourly_stats")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Monitoring
# MAGIC Query stream status to monitor processing

# COMMAND ----------

# Monitor stream health
# GOOD: Built-in monitoring
display(spark.streams.active)
