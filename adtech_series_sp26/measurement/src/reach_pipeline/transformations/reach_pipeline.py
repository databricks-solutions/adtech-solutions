from functools import reduce
from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql import Window

# ---------------------------------------------------------------------------
# Pipeline parameters
# Defined in resources/reach_pipeline.pipeline.yml under configuration:
# ---------------------------------------------------------------------------
source_catalog    = spark.conf.get("source_catalog")     # media_advertising
source_schema     = spark.conf.get("source_schema")      # bronze
source_table      = spark.conf.get("source_table")       # impression_logs_prod
campaigns_catalog = spark.conf.get("campaigns_catalog")  # media_advertising
campaigns_schema  = spark.conf.get("campaigns_schema")   # segments
campaigns_table   = spark.conf.get("campaigns_table")    # megacorp_campaigns

# ---------------------------------------------------------------------------
# IFA prefix helpers
# Both device_type and inventory_type are derived from the same source column
# (request_kv._server_ifa) but use different CASE WHEN logic and different
# fallback values: device_type falls back to "Web"; inventory_type to "Other".
#
# IFA prefixes → device classification:
#   rida, tifa, vida, afai, lgudid  → CTV   (connected TV identifiers)
#   idfa, aaid                      → Mobile (mobile ad identifiers)
#   all others / NULL               → Web    (device_type) or Other (inventory_type)
# ---------------------------------------------------------------------------
_CTV_PREFIXES    = ["rida", "tifa", "vida", "afai", "lgudid"]
_MOBILE_PREFIXES = ["idfa", "aaid"]

def _ifa_prefix_col():
    """Extract the prefix (part before ':') from request_kv._server_ifa."""
    return F.split(F.col("request_kv._server_ifa"), ":")[0]


def _device_type_col():
    """CTV / Mobile / Web — device environment dimension."""
    p = _ifa_prefix_col()
    return (
        F.when(p.isin(_CTV_PREFIXES),    F.lit("CTV"))
         .when(p.isin(_MOBILE_PREFIXES), F.lit("Mobile"))
         .otherwise(F.lit("Web"))
    )


def _inventory_type_col():
    """CTV / Mobile / Other — ad inventory channel dimension.

    Identical CTV/Mobile mapping to device_type, but the fallback is 'Other'
    (not 'Web') because web/unknown inventory is categorised as open/standard.
    CTV inventory is predominantly purchased as guaranteed deals (premium).
    """
    p = _ifa_prefix_col()
    return (
        F.when(p.isin(_CTV_PREFIXES),    F.lit("CTV"))
         .when(p.isin(_MOBILE_PREFIXES), F.lit("Mobile"))
         .otherwise(F.lit("Other"))
    )


# ---------------------------------------------------------------------------
# Step 1a: COPPA filter + audience join + struct flatten + enrichment
#
# @dp.temporary_view — no catalog table created.
# Exists only within the pipeline execution context.
#
# Filters applied (in order of earliest exclusion):
#   1. request_kv._is_coppa == False  — exclude COPPA-flagged records first
#   2. meta_info.is_target  == True   — retain only audience-matched impressions
#   3. INNER JOIN megacorp_campaigns  — brings in megacorp_hhid (household ID)
#
# Enrichment:
#   - device_type      from IFA prefix → CTV / Mobile / Web
#   - inventory_type   from IFA prefix → CTV / Mobile / Other (separate CASE WHEN)
#   - marketing_region via LEFT JOIN on zip3_marketing_region (ZIP3 prefix lookup)
#   - ip_address       retained as-is for IP reach deduplication
#   - server_email     from request_kv._server_email for email reach deduplication
# ---------------------------------------------------------------------------
@dp.temporary_view(name="reach_impressions_filtered")
def reach_impressions_filtered():
    impressions = (
        spark.read.table(f"{source_catalog}.{source_schema}.{source_table}")
        .filter(F.col("request_kv._is_coppa") == False)
        .filter(F.col("meta_info.is_target") == True)
    )

    # Deduplicate the audience table — one row per (individual, campaign)
    audience = (
        spark.read.table(f"{campaigns_catalog}.{campaigns_schema}.{campaigns_table}")
        .select("megacorp_indid", "megacorp_hhid", "campaign_name")
        .dropDuplicates(["megacorp_indid", "campaign_name"])
    )

    # ZIP3 → marketing region lookup; alias avoids column name ambiguity after join
    zip_lookup = (
        spark.read.table("media_advertising.gold.zip3_marketing_region")
        .select(F.col("zip3"), F.col("marketing_region").alias("_marketing_region"))
    )

    return (
        impressions
        .join(audience, on=["megacorp_indid", "campaign_name"], how="inner")
        .join(zip_lookup, on=F.substring(F.col("user_zip"), 1, 3) == F.col("zip3"), how="left")
        .select(
            "impression_id",
            "date",
            F.col("distributor_name").alias("publisher"),
            F.col("campaign_name").alias("campaign"),
            F.col("megacorp_indid").alias("mc_indid"),
            F.col("megacorp_hhid").alias("hhid"),
            F.col("content_nm").alias("content"),
            "ip_address",
            F.col("request_kv._server_email").alias("server_email"),
            _device_type_col().alias("device_type"),
            _inventory_type_col().alias("inventory_type"),
            F.coalesce(F.col("_marketing_region"), F.lit("Other")).alias("marketing_region"),
        )
    )


# ---------------------------------------------------------------------------
# Step 1b: Raw impression counts by dimension — for raw_imps in gold cube
#
# @dp.temporary_view — no catalog table created.
#
# Reads impression_logs_prod WITHOUT the COPPA filter and WITHOUT the audience
# join. Applies the same IFA-prefix enrichment and ZIP3 lookup so that raw_imps
# aligns with the same dimension grain as the filtered silver metrics.
#
# Aggregates to: (campaign, publisher, content, device_type, inventory_type,
#                 marketing_region) → raw impression count.
#
# The gold cube LEFT JOINs this view to add raw_imps alongside matched_imps.
# raw_imps will always be >= matched_imps for every row (COPPA + join reduce).
# ---------------------------------------------------------------------------
@dp.temporary_view(name="raw_impressions_by_dim")
def raw_impressions_by_dim():
    zip_lookup = (
        spark.read.table("media_advertising.gold.zip3_marketing_region")
        .select(F.col("zip3"), F.col("marketing_region").alias("_marketing_region"))
    )

    return (
        spark.read.table(f"{source_catalog}.{source_schema}.{source_table}")
        .join(zip_lookup, on=F.substring(F.col("user_zip"), 1, 3) == F.col("zip3"), how="left")
        .select(
            F.col("campaign_name").alias("campaign"),
            F.col("distributor_name").alias("publisher"),
            F.col("content_nm").alias("content"),
            _device_type_col().alias("device_type"),
            _inventory_type_col().alias("inventory_type"),
            F.coalesce(F.col("_marketing_region"), F.lit("Other")).alias("marketing_region"),
            "impression_id",
        )
        .groupBy("campaign", "publisher", "content", "device_type", "inventory_type", "marketing_region")
        .agg(F.count("impression_id").alias("raw_imps"))
    )


# ---------------------------------------------------------------------------
# Step 2: Silver — individual-level daily aggregation
#
# @dp.materialized_view — full refresh on each pipeline run.
# One row per (date × mc_indid × hhid × ip_address × server_email ×
#              publisher × device_type × inventory_type × campaign × content ×
#              marketing_region).
#
# ip_address and server_email are carried through the GROUP BY so the gold
# cube can COUNT(DISTINCT ...) them accurately across all dates.
#
# Writes to: media_advertising.silver.reach_impressions
#   (fully-qualified name in decorator overrides the pipeline-level gold default)
# ---------------------------------------------------------------------------
@dp.materialized_view(
    name="media_advertising.silver.reach_impressions",
    comment=(
        "Individual-level daily impression aggregation. COPPA-filtered. "
        "One row per mc_indid × hhid × ip_address × server_email × publisher × "
        "device_type × inventory_type × campaign × content × marketing_region × date. "
        "Source of truth for gold reach_cube — never query impression_logs_prod directly."
    ),
    cluster_by=["date"],
)
def reach_impressions():
    return (
        spark.read.table("reach_impressions_filtered")
        .groupBy(
            "date",
            "mc_indid",
            "hhid",
            "ip_address",
            "server_email",
            "publisher",
            "device_type",
            "inventory_type",
            "campaign",
            "content",
            "marketing_region",
        )
        .agg(F.count("impression_id").alias("imps"))
    )


# ---------------------------------------------------------------------------
# Step 3: Silver — campaign-level aggregation with identity array strings
#
# @dp.materialized_view — full refresh on each pipeline run.
#
# Reads from:
#   - media_advertising.silver.reach_impressions  (individual-level daily rows)
#   - raw_impressions_by_dim                       (pre-filter raw counts, LEFT JOINed)
#
# Writes to: media_advertising.silver.reach_prelim
#
# One row per 6-dimension combination (no date). Identity keys are stored as
# comma-joined strings via array_join(collect_set(...)), enabling correct
# cross-combo deduplication in reach_cube rollup rows via
# array_distinct(flatten(collect_list(split(...)))).
# ---------------------------------------------------------------------------
@dp.materialized_view(
    name="media_advertising.silver.reach_prelim",
    comment=(
        "Campaign-level aggregation with no date dimension. "
        "One row per (campaign × publisher × device_type × inventory_type × content × marketing_region). "
        "Identity keys stored as comma-joined strings (array_join(collect_set(...))) enabling correct "
        "cross-combo deduplication via array_distinct(flatten(split(...))) in reach_cube rollup rows."
    ),
    cluster_by=["campaign", "publisher"],
)
def reach_prelim():
    _join_keys = ["campaign", "publisher", "device_type", "inventory_type", "content", "marketing_region"]
    raw = spark.read.table("raw_impressions_by_dim")
    return (
        spark.read.table("media_advertising.silver.reach_impressions")
        .groupBy(*_join_keys)
        .agg(
            F.array_join(F.collect_set("mc_indid"),    ",").alias("ind_ids"),
            F.array_join(F.collect_set("hhid"),         ",").alias("hhid_ids"),
            F.array_join(F.collect_set("ip_address"),   ",").alias("ip_ids"),
            F.array_join(F.collect_set("server_email"), ",").alias("email_ids"),
            F.sum("imps").alias("matched_imps"),
        )
        .join(raw, on=_join_keys, how="left")
    )


# ---------------------------------------------------------------------------
# Step 4: Gold — reach cube with detail rows + rollup rows
#
# @dp.materialized_view — full refresh on each pipeline run.
#
# Reads from: media_advertising.silver.reach_prelim
#
# Writes to: media_advertising.gold.reach_cube
# Liquid Clustering on (campaign, publisher).
#
# Two passes UNION ALL'd:
#   Pass 1 — detail rows: one per 6-dim combination, reach counts from string lengths
#   Pass 2 — rollup rows: 6 rollup levels (one dim kept, rest = 'All'), plus
#             campaign-total row (all dims = 'All') which replaces reach_totals.
#
# Rollup deduplication uses array_distinct(flatten(collect_list(split(...)))) —
# mathematically correct across any dimension combination.
# ---------------------------------------------------------------------------
@dp.materialized_view(
    name="reach_cube",
    comment=(
        "Reach metrics with detail rows (all 6 dims specific) and rollup rows (collapsed dims = 'All'). "
        "Campaign-total rollup row (all dims = 'All') replaces reach_totals. "
        "Rollup rows use array_distinct(flatten(...)) deduplication — correct at any grain. "
        "COPPA-filtered. Do NOT query impression_logs_prod directly."
    ),
    cluster_by=["campaign", "publisher"],
)
def reach_cube():
    _all_cols = ["campaign", "publisher", "device_type", "inventory_type", "content", "marketing_region"]

    prelim = spark.read.table("media_advertising.silver.reach_prelim")

    # Pass 1: detail rows — reach counts derived from string lengths (size of comma-split array)
    detail = prelim.select(
        "campaign", "publisher", "device_type", "inventory_type", "content", "marketing_region",
        F.size(F.split(F.col("ind_ids"),   ",")).alias("reach_ind"),
        F.size(F.split(F.col("hhid_ids"),  ",")).alias("reach_hhid"),
        F.size(F.split(F.col("ip_ids"),    ",")).alias("reach_ip"),
        F.size(F.split(F.col("email_ids"), ",")).alias("reach_email"),
        "matched_imps",
        "raw_imps",
    )

    # Pass 2: rollup rows — merge identity arrays, deduplicate, count
    def _rollup(df, group_cols):
        return (
            df.groupBy(*group_cols)
            .agg(
                F.size(F.array_distinct(F.flatten(F.collect_list(F.split(F.col("ind_ids"),   ","))))).alias("reach_ind"),
                F.size(F.array_distinct(F.flatten(F.collect_list(F.split(F.col("hhid_ids"),  ","))))).alias("reach_hhid"),
                F.size(F.array_distinct(F.flatten(F.collect_list(F.split(F.col("ip_ids"),    ","))))).alias("reach_ip"),
                F.size(F.array_distinct(F.flatten(F.collect_list(F.split(F.col("email_ids"), ","))))).alias("reach_email"),
                F.sum("matched_imps").alias("matched_imps"),
                F.sum("raw_imps").alias("raw_imps"),
            )
            .select(
                *[F.col(c) if c in group_cols else F.lit("All").alias(c) for c in _all_cols],
                "reach_ind", "reach_hhid", "reach_ip", "reach_email", "matched_imps", "raw_imps",
            )
        )

    rollups = [
        # Per-campaign rollups (campaign always specific)
        _rollup(prelim, ["campaign", "publisher"]),
        _rollup(prelim, ["campaign", "device_type"]),
        _rollup(prelim, ["campaign", "inventory_type"]),
        _rollup(prelim, ["campaign", "content"]),
        _rollup(prelim, ["campaign", "marketing_region"]),
        _rollup(prelim, ["campaign"]),  # campaign-total row — replaces reach_totals
        # Cross-campaign rollups (campaign='All') — enables 'All' in campaign filter
        _rollup(prelim, ["publisher"]),
        _rollup(prelim, ["device_type"]),
        _rollup(prelim, ["inventory_type"]),
        _rollup(prelim, ["content"]),
        _rollup(prelim, ["marketing_region"]),
        _rollup(prelim, []),            # grand total — all dims = 'All'
    ]

    return reduce(lambda a, b: a.unionAll(b), [detail] + rollups)


# ---------------------------------------------------------------------------
# Step 5: Gold — individual-level gold table for UCMV
#
# @dp.materialized_view — full refresh on each pipeline run.
#
# Reads from:
#   - media_advertising.silver.reach_impressions  (individual rows)
#   - raw_impressions_by_dim                       (pre-filter raw counts, LEFT JOINed)
#
# Writes to: media_advertising.gold.reach_individual
#
# One row per mc_indid × dimension combination. Used as source for the
# campaign_reach_metrics Metric View, enabling COUNT(DISTINCT ...) measures
# at any query grain without double-counting.
#
# raw_imps_kpi: ROW_NUMBER() marks the first individual per dimension
# combination as the carrier of raw_imps. SUM(raw_imps_kpi) is additive
# and correct at any grain.
# ---------------------------------------------------------------------------
@dp.materialized_view(
    name="reach_individual",
    comment=(
        "Individual-level gold table. One row per mc_indid × dimension combination. "
        "Used as source for campaign_reach_metrics UCMV to enable COUNT(DISTINCT ...) "
        "measures at any query grain. raw_imps_kpi attributes raw impression counts to "
        "one row per dimension combination via ROW_NUMBER, making SUM(raw_imps_kpi) "
        "correct at any grain."
    ),
    cluster_by=["campaign", "publisher"],
)
def reach_individual():
    _join_keys = ["campaign", "publisher", "content", "device_type", "inventory_type", "marketing_region"]

    w = Window.partitionBy(*_join_keys).orderBy("mc_indid")

    silver = spark.read.table("media_advertising.silver.reach_impressions")
    raw = spark.read.table("raw_impressions_by_dim")

    return (
        silver
        .join(raw, on=_join_keys, how="left")
        .withColumn("rn", F.row_number().over(w))
        .withColumn(
            "raw_imps_kpi",
            F.when(F.col("rn") == 1, F.col("raw_imps")).otherwise(F.lit(0)),
        )
        .drop("rn", "raw_imps")
    )


# reach_totals removed (Phase 11 / T052).
# Campaign-total reach is now the rollup row in reach_cube where all dims = 'All'.
# Use: SELECT reach_ind FROM reach_cube WHERE campaign = ? AND publisher = 'All'
#        AND device_type = 'All' AND inventory_type = 'All'
#        AND content = 'All' AND marketing_region = 'All'
