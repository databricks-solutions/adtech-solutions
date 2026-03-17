# Databricks notebook source
# MAGIC %md
# MAGIC # Impression Logs DLT Pipeline
# MAGIC
# MAGIC This pipeline processes impression logs from the bronze layer through silver and gold layers.
# MAGIC
# MAGIC **Data Flow:**
# MAGIC - **Bronze**: `media_advertising.bronze.raw_impression_logs` (append-only event stream)
# MAGIC - **Silver**: `media_advertising.silver.megacorp_impressions` (streaming windowed aggregation — daily user-grain)
# MAGIC - **Gold**: `media_advertising.gold.megacorp_user_frequency` (materialized view)

# COMMAND ----------

import dlt
from pyspark.sql import functions as F

# =============================================================================
# BRONZE TO SILVER - Transformed View
# =============================================================================

@dlt.view(
    comment="Transformed bronze impression logs - flattens structs and derives device type"
)
def bronze_transformed():
    """
    Reads from bronze table as an append-only stream.
    Flattens nested structures and adds derived columns.
    """
    return (
        spark.readStream
        .table("media_advertising.bronze.raw_impression_logs")
        .select(
            F.col("impression_id"),
            F.col("date"),
            F.col("timestamp").alias("event_timestamp"),
            F.col("distributor_name"),
            F.col("campaign_name"),
            F.col("content_id"),
            F.col("content_nm"),
            F.col("megacorp_indid"),
            F.col("request_kv._server_email").alias("email_sha256"),
            F.col("request_kv._server_ifa").alias("device_ifa"),
            F.col("request_kv._is_coppa").alias("is_coppa"),
            F.col("meta_info.has_correct_geo"),
            F.col("meta_info.has_correct_linkage"),
            F.col("meta_info.is_target"),
            F.col("ip_address"),
            F.col("user_zip"),
            F.col("user_state"),
            F.when(F.col("megacorp_indid").isNotNull(), "matched")
            .otherwise("unmatched").alias("identity_status"),
            F.when(F.col("request_kv._server_ifa").isNotNull(),
                   F.split(F.col("request_kv._server_ifa"), ":")[0]).alias("ifa_type"),
            F.when(
                F.split(F.col("request_kv._server_ifa"), ":")[0].isin("roku_ifa", "amazon_fire_id"),
                F.lit("CTV")
            ).when(
                F.split(F.col("request_kv._server_ifa"), ":")[0].isin("apple_idfa", "google_adid"),
                F.lit("Mobile")
            ).otherwise(F.lit("Web")).alias("device_type")
        )
    )


# =============================================================================
# SILVER - Streaming Windowed Aggregation (daily user-grain)
# =============================================================================

@dlt.table(
    name="media_advertising.silver.megacorp_impressions",
    comment="Daily user-grain streaming aggregation with watermark",
    table_properties={"quality": "silver"}
)
def silver_daily_user_impressions():
    return (
        dlt.read_stream("bronze_transformed")
        .withWatermark("event_timestamp", "2 hours")
        .groupBy(
            F.window("event_timestamp", "1 day").alias("date_window"),
            "megacorp_indid",
            "distributor_name",
            "device_type",
            "campaign_name",
            "content_nm"
        )
        .agg(F.count("*").alias("imps"))
    )


# =============================================================================
# GOLD - Frequency Analysis (materialized view over silver)
# =============================================================================

@dlt.table(
    name="media_advertising.gold.megacorp_user_frequency",
    comment="Impression frequency per user per campaign",
    table_properties={"quality": "gold"}
)
def gold_user_frequency():
    return (
        dlt.read("media_advertising.silver.megacorp_impressions")
        .filter(F.col("megacorp_indid").isNotNull())
        .groupBy("campaign_name", "megacorp_indid")
        .agg(
            F.sum("imps").alias("impression_count"),
            F.min("date_window.start").alias("first_seen"),
            F.max("date_window.start").alias("last_seen")
        )
    )
