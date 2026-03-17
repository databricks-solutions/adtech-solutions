# Databricks notebook source

# COMMAND ----------

# MAGIC %md
# MAGIC # Kafka Producer - Ad Impression Log Generator
# MAGIC
# MAGIC Generates synthetic ad impression events using `dbldatagen` in streaming mode,
# MAGIC serializes as Avro, and publishes to Kafka (MSK via SSL).

# COMMAND ----------

dbutils.widgets.text("catalog", "media_advertising")
dbutils.widgets.text("schema", "realtime")
dbutils.widgets.text("kafka_topic", "tanner_wendland_adtech_impressions_realtime_v3")
dbutils.widgets.text("kafka_secret_scope", "oetrta")
dbutils.widgets.text("kafka_secret_key", "kafka-bootstrap-servers-tls")
dbutils.widgets.text("records_per_second", "100")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
kafka_topic = dbutils.widgets.get("kafka_topic")
kafka_secret_scope = dbutils.widgets.get("kafka_secret_scope")
kafka_secret_key = dbutils.widgets.get("kafka_secret_key")
records_per_second = int(dbutils.widgets.get("records_per_second"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Avro Schema
# MAGIC
# MAGIC Simplified impression schema — core fields only, no deep nested structs.

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
# MAGIC ## Build Streaming DataFrame with dbldatagen

# COMMAND ----------

import dbldatagen as dg
from pyspark.sql import functions as F
from pyspark.sql.avro.functions import to_avro

distributors = ["StreamTV", "CableMax", "WebAds", "MobileFirst", "CTVNetwork"]
distributor_weights = [30, 25, 20, 15, 10]

campaigns = [
    "Happy Dogs",
    "Terrific Tacos",
    "Best Burgers",
    "Cool Car",
    "Super Savings",
    "Fresh Flowers",
    "Moving Movie",
]

states = ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]

devices = ["Web", "Mobile", "CTV"]
device_weights = [40, 35, 25]

spec = (
    dg.DataGenerator(spark, rows=1000, partitions=4)
    .withColumn("impression_id", "long", uniqueValues=1_000_000_000, random=True)
    .withColumn(
        "distributor_name",
        "string",
        values=distributors,
        weights=distributor_weights,
        random=True,
    )
    .withColumn(
        "campaign_name", "string", values=campaigns, random=True
    )
    .withColumn("content_id_num", "int", minValue=1000, maxValue=9999, random=True)
    .withColumn("content_name_num", "int", minValue=1, maxValue=500, random=True)
    .withColumn(
        "device_type",
        "string",
        values=devices,
        weights=device_weights,
        random=True,
    )
    .withColumn("ip_octet1", "int", minValue=1, maxValue=254, random=True)
    .withColumn("ip_octet2", "int", minValue=0, maxValue=254, random=True)
    .withColumn("ip_octet3", "int", minValue=0, maxValue=254, random=True)
    .withColumn("ip_octet4", "int", minValue=1, maxValue=254, random=True)
    .withColumn("zip_num", "int", minValue=10000, maxValue=99999, random=True)
    .withColumn("zip_null_flag", "float", minValue=0.0, maxValue=1.0, random=True)
    .withColumn(
        "user_state",
        "string",
        values=states,
        random=True,
        percentNulls=0.15,
    )
    .withColumn("mcid_num", "int", minValue=100000, maxValue=999999, random=True)
    .withColumn("mcid_null_flag", "float", minValue=0.0, maxValue=1.0, random=True)
)

streaming_df = spec.build(withStreaming=True, options={"rowsPerSecond": records_per_second})

# COMMAND ----------

# MAGIC %md
# MAGIC ## Transform and Publish to Kafka

# COMMAND ----------

output_df = streaming_df.select(
    F.col("impression_id"),
    (F.unix_micros(F.current_timestamp())).alias("timestamp"),
    F.col("distributor_name"),
    F.col("campaign_name"),
    F.concat(F.lit("content_"), F.col("content_id_num").cast("string")).alias(
        "content_id"
    ),
    F.concat(F.lit("Content Show "), F.col("content_name_num").cast("string")).alias(
        "content_name"
    ),
    F.col("device_type"),
    F.concat_ws(
        ".",
        F.col("ip_octet1").cast("string"),
        F.col("ip_octet2").cast("string"),
        F.col("ip_octet3").cast("string"),
        F.col("ip_octet4").cast("string"),
    ).alias("ip_address"),
    F.when(F.col("zip_null_flag") < 0.15, F.lit(None))
    .otherwise(F.col("zip_num").cast("string"))
    .alias("user_zip"),
    F.col("user_state"),
    F.when(F.col("mcid_null_flag") < 0.40, F.lit(None))
    .otherwise(F.concat(F.lit("MCID_"), F.col("mcid_num").cast("string")))
    .alias("megacorp_indid"),
)

kafka_df = output_df.select(
    to_avro(F.struct("*"), avro_schema).alias("value")
)

# COMMAND ----------

kafka_bootstrap_servers = dbutils.secrets.get(kafka_secret_scope, kafka_secret_key)

query = (
    kafka_df.writeStream.format("kafka")
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers)
    .option("kafka.security.protocol", "SSL")
    .option("topic", kafka_topic)
    .option("checkpointLocation", f"/Volumes/{catalog}/{schema}/checkpoints/{kafka_topic}/producer")
    .start()
)

print(f"Publishing to Kafka topic: {kafka_topic}")
print(f"Rate: {records_per_second} records/second")

query.awaitTermination()
