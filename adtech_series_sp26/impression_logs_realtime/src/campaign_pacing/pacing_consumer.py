# Databricks notebook source

# COMMAND ----------

# MAGIC %md
# MAGIC # Campaign Pacing Consumer
# MAGIC
# MAGIC Reads raw ad impression events (Avro) from Kafka, enriches with derived fields,
# MAGIC counts impressions per campaign using Spark Real-Time Mode (RTM) stateful aggregation,
# MAGIC and writes running totals to Lakebase via the **JDBC Streaming Sink** (Private Preview)
# MAGIC — delivering ~1–5s update latency.
# MAGIC
# MAGIC **Pipeline:**
# MAGIC ```
# MAGIC Kafka (raw Avro)
# MAGIC   → deserialize Avro → enrich (identity, premium, geo)
# MAGIC   → extract campaign_name
# MAGIC   → broadcast join with budget metadata (static)
# MAGIC   → groupBy campaign_name → impression count  (stateful, RTM)
# MAGIC   → jdbcStreaming → Lakebase (upsert on campaign_name, flush every 50ms)
# MAGIC ```
# MAGIC
# MAGIC **Prerequisites:**
# MAGIC - Table is created by the campaign pacing app on startup
# MAGIC - Cluster must have `spark.sql.streaming.jdbc.enabled = true` (set in job YAML)
# MAGIC - Dedicated cluster only — serverless not supported in PrPr

# COMMAND ----------

dbutils.widgets.text("catalog",               "media_advertising")
dbutils.widgets.text("schema",                "bronze")
dbutils.widgets.text("kafka_topic",           "tanner_wendland_adtech_impressions_realtime_v3")
dbutils.widgets.text("kafka_secret_scope",    "oetrta")
dbutils.widgets.text("kafka_secret_key",      "kafka-bootstrap-servers-tls")
dbutils.widgets.text("lakebase_instance_name", "campaign-pacing")
dbutils.widgets.text("lakebase_db_name",      "databricks_postgres")

catalog               = dbutils.widgets.get("catalog")
schema                = dbutils.widgets.get("schema")
kafka_topic           = dbutils.widgets.get("kafka_topic")
kafka_secret_scope    = dbutils.widgets.get("kafka_secret_scope")
kafka_secret_key      = dbutils.widgets.get("kafka_secret_key")
lakebase_instance     = dbutils.widgets.get("lakebase_instance_name")
lakebase_db           = dbutils.widgets.get("lakebase_db_name")

checkpoint_path = f"/Volumes/{catalog}/{schema}/checkpoints/{kafka_topic}/pacing_consumer"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature Flag + Kafka Bootstrap

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.avro.functions import from_avro
from pyspark.sql.functions import broadcast, count, current_timestamp

# PrPr feature flag — also set on the cluster via spark_conf in job YAML
spark.conf.set("spark.sql.streaming.jdbc.enabled", "true")

kafka_bootstrap_servers = dbutils.secrets.get(kafka_secret_scope, kafka_secret_key)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Avro Schema
# MAGIC
# MAGIC Must match the producer schema exactly.

# COMMAND ----------

avro_schema = """
{
  "type": "record",
  "name": "AdImpression",
  "namespace": "com.adtech.impressions",
  "fields": [
    {"name": "impression_id", "type": "long"},
    {"name": "timestamp", "type": {"type": "long", "logicalType": "timestamp-micros"}},
    {"name": "distributor_name", "type": "string"},
    {"name": "campaign_name", "type": "string"},
    {"name": "content_id", "type": "string"},
    {"name": "content_name", "type": "string"},
    {"name": "device_type", "type": "string"},
    {"name": "ip_address", "type": "string"},
    {"name": "user_zip", "type": ["null", "string"], "default": null},
    {"name": "user_state", "type": ["null", "string"], "default": null},
    {"name": "megacorp_indid", "type": ["null", "string"], "default": null}
  ]
}
"""

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Read Raw Events from Kafka and Enrich
# MAGIC
# MAGIC Deserialize Avro, add derived enrichment columns (identity status, premium flag,
# MAGIC geo completeness), then extract only `campaign_name` for the aggregation.

# COMMAND ----------

stream_df = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers)
    .option("kafka.security.protocol", "SSL")
    .option("subscribe", kafka_topic)
    .option("startingOffsets", "earliest")
    .option("failOnDataLoss", "false")
    .load()
    .select(from_avro(F.col("value"), avro_schema).alias("data"))
    .select("data.*")
    .withColumnRenamed("timestamp", "event_timestamp")
    .withColumn("ingestion_timestamp", F.current_timestamp())
    .withColumn(
        "identity_status",
        F.when(F.col("megacorp_indid").isNotNull(), "matched")
         .otherwise("unmatched")
    )
    .withColumn(
        "is_premium",
        F.col("device_type") == "CTV"
    )
    .withColumn(
        "geo_complete",
        F.col("user_state").isNotNull() & F.col("user_zip").isNotNull()
    )
    .withColumn("processing_timestamp", F.current_timestamp())
    .select("campaign_name")
    .filter(F.col("campaign_name").isNotNull())
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Stream-Static Broadcast Join
# MAGIC
# MAGIC Budget metadata is tiny (7 rows) and never changes during a run — ideal for a
# MAGIC broadcast join. Carrying budget columns through the join lets us pass them to
# MAGIC Lakebase without a separate lookup at write time.

# COMMAND ----------

campaign_budgets = spark.createDataFrame(
    [
        ("Happy Dogs",      6_000_000,  8.0, 48000.0),
        ("Terrific Tacos",  3_000_000, 12.0, 36000.0),
        ("Best Burgers",    3_600_000, 10.0, 36000.0),
        ("Cool Car",        2_000_000, 15.0, 30000.0),
        ("Super Savings",   1_200_000, 10.0, 12000.0),
        ("Fresh Flowers",   1_200_000,  7.0,  8400.0),
        ("Moving Movie",    2_000_000, 12.0, 24000.0),
    ],
    ["campaign_name", "budget_imps", "cpm_rate", "budget_dollars"],
)

enriched = stream_df.join(broadcast(campaign_budgets), "campaign_name", "left")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Stateful Count per Campaign
# MAGIC
# MAGIC `groupBy` in RTM update mode maintains incremental state across micro-batches.
# MAGIC Budget columns are included in the groupBy key so they flow through to the sink.

# COMMAND ----------

pacing = (
    enriched
    .groupBy("campaign_name", "budget_imps", "cpm_rate", "budget_dollars")
    .agg(count("*").alias("impression_count"))
    .withColumn("last_updated", current_timestamp())
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Write to Lakebase via JDBC Streaming Sink
# MAGIC
# MAGIC - `instancename` — auto-generates and refreshes OAuth credentials each micro-batch
# MAGIC - `upsertkey` — must have a PRIMARY KEY on the table (created by the app on startup)
# MAGIC - `batchinterval` — flushes buffered rows every 50ms (critical for RTM latency)
# MAGIC - `trigger(realTime=...)` — RTM continuous processing; JDBC batchinterval drives write cadence

# COMMAND ----------

query = (
    pacing.writeStream
    .format("jdbcStreaming")
    .option("instancename",       lakebase_instance)
    .option("dbname",             lakebase_db)
    .option("dbtable",            "campaign_pacing")
    .option("upsertkey",          "campaign_name")
    .option("batchinterval",      "50 milliseconds")
    .option("checkpointLocation", checkpoint_path)
    .outputMode("update")
    .trigger(realTime="5 minutes")
    .start()
)

print(f"Consuming from : {kafka_topic}")
print(f"Lakebase       : {lakebase_instance}/{lakebase_db}/campaign_pacing")
print(f"Checkpoint     : {checkpoint_path}")
print(f"Trigger        : realTime=5 minutes (RTM) + batchinterval=50ms (JDBC flush)")

query.awaitTermination()
