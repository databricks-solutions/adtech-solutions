# Databricks for Ad Tech — Measurement

Session 4 of the Databricks for Ad Tech Spring 2026 series. Computes deduplicated ad-campaign reach via a Spark Declarative Pipeline (COPPA filter → pre-aggregated reach cube), exposes it through a Unity Catalog Function and a governed Metric View, and surfaces results in an AI/BI dashboard and a Genie space.

## Overview

After ad events have been ingested and governed (Session 3), the measurement layer answers the question every advertiser asks: *who did we actually reach?* This project shows how to compute deduplicated reach at any grain (individual / household / IP / email), expose it as a governed semantic layer, and let business users explore it visually and in natural language — all on Databricks.

The sample dataset uses a fictional media conglomerate, MegaCorp, running 7 ad campaigns across CTV, mobile, and web.

## Architecture

```
<catalog>.bronze.impression_logs_prod   (source impressions, read-only)
<catalog>.segments.megacorp_campaigns   (audience list, read-only)
    │
    │  Spark Declarative Pipeline
    │  COPPA filter → audience match → struct enrichment
    │
    ▼
<catalog>.silver.reach_impressions      (individual daily aggregation)
<catalog>.silver.reach_prelim           (campaign-level identity string aggregation)
    │
    ▼
<catalog>.gold.reach_cube               (detail rows + 12 rollup levels)
<catalog>.gold.reach_individual         (individual-level rows; Metric View source)
    │
    ├── <catalog>.gold.compute_reach          (UC Function — scalar reach count)
    ├── <catalog>.gold.campaign_reach_metrics (Metric View — governed semantic layer)
    ├── AI/BI Dashboard  (campaign_reach.lvdash.json)
    └── Genie Space      (campaign_reach_qa.json)
```

## Databricks Features Demonstrated

| Feature | Where used |
|---|---|
| Spark Declarative Pipelines (SDP) | `src/reach_pipeline/transformations/reach_pipeline.py` |
| Unity Catalog Metric Views (DBR 17.2+, YAML v1.1) | `metric_views/campaign_reach_metrics.sql` |
| Unity Catalog Functions | `functions/compute_reach.sql` |
| AI/BI Dashboards as bundle resources | `resources/campaign_reach.dashboard.yml` + `src/dashboards/campaign_reach.lvdash.json` |
| Genie Spaces (REST API authoring + round-trip) | `genie_spaces/` |
| Databricks Asset Bundles | `databricks.yml` |
| Serverless compute + Photon | `resources/reach_pipeline.pipeline.yml` |
| Pre-aggregated rollup cube for sub-5s dashboard load | `reach_cube` table |

## Prerequisites

| Requirement | Details |
|---|---|
| Databricks workspace | DBR 17.2+ serverless runtime (required for Unity Catalog Metric Views) |
| Unity Catalog | Enabled; target catalog/schema must exist |
| Databricks CLI | Authenticated against your workspace |
| Permissions | `CREATE TABLE`, `CREATE FUNCTION`, `CREATE VIEW` on the target schemas |
| Python | 3.11+, with `databricks-sdk` (for the Genie deploy script) |
| Source data | `<catalog>.bronze.impression_logs_prod` (impressions) and `<catalog>.segments.megacorp_campaigns` (audience). All locations are overridable via bundle variables. |

> **Note on catalog naming.** SQL files in `functions/`, `metric_views/`, and `tables/` reference `media_advertising.gold` directly. To deploy under a different catalog or schema, either create the `media_advertising` catalog or substitute names with `sed` before running the SQL execute commands. The bundle pipeline (`databricks.yml`) is fully parameterized via the `catalog` / `source_*` / `campaigns_*` variables.

## Deployment

All commands assume a Databricks CLI profile is configured against your workspace. Set `DATABRICKS_CONFIG_PROFILE=<profile>` or pass `--profile <profile>` (omitted below for brevity).

```bash
# 1. Lookup table (ZIP3 → marketing region)
databricks sql execute --warehouse-id <warehouse_id> --file tables/zip3_marketing_region.sql

# 2. UC Function + Metric View
databricks sql execute --warehouse-id <warehouse_id> --file functions/compute_reach.sql
databricks sql execute --warehouse-id <warehouse_id> --file metric_views/campaign_reach_metrics.sql

# 3. Pipeline + Dashboard (bundle deploys both; pipeline run populates tables)
databricks bundle deploy --var warehouse_id=<warehouse_id>
databricks bundle run reach_pipeline

# 4. Genie space (fresh create — prints space_id + URL)
python genie_spaces/deploy_genie_space.py \
  --parent-path "/Shared/Adtech-measurement" \
  --warehouse-id <warehouse_id>
```

End-to-end walkthrough with verification queries: [docs/quickstart.md](docs/quickstart.md).

## Repository Structure

```
databricks.yml                           # Bundle config — variables + dev/prod targets
resources/
├── reach_pipeline.pipeline.yml          # Pipeline resource definition
└── campaign_reach.dashboard.yml         # Dashboard resource definition
src/
├── reach_pipeline/transformations/
│   └── reach_pipeline.py                # Pipeline transformations (Python SDP)
└── dashboards/
    └── campaign_reach.lvdash.json       # AI/BI Dashboard definition
functions/
└── compute_reach.sql                    # UC Function — scalar reach count
metric_views/
└── campaign_reach_metrics.sql           # Metric View — governed semantic layer
tables/
└── zip3_marketing_region.sql            # ZIP3 → marketing region lookup table
genie_spaces/
├── campaign_reach_qa.json               # Space config (instructions, SQL examples, benchmarks)
├── deploy_genie_space.py                # Create or update via REST API
└── eval_genie_space.py                  # Verifies question routing (11 cases)
docs/
└── quickstart.md                        # Step-by-step deployment + verification
```

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Pipeline type | Spark Declarative Pipeline (batch) | `COUNT DISTINCT` requires a full scan; streaming adds no benefit |
| COPPA filter | Earliest step (temp view) | Flagged records must never enter any aggregation |
| Reach deduplication | Individual identity key | Present on every impression row; enables correct `COUNT DISTINCT` |
| Metric View source | Individual-level table (`reach_individual`) | `COUNT DISTINCT` correct at any query grain — pre-aggregated rows would double-count individuals across dimension combinations |
| Dashboard datasets | Individual-level (KPIs) + cube (Explorer) | KPIs require correct deduplication; Explorer benefits from pre-aggregated rollup rows |
| Genie data sources | Metric View (primary) + reach cube (impression-volume queries) | `MEASURE()` syntax for reach; cube as the only source for `raw_imps` |

## Series Context

This is **Session 4 of 4** in the Databricks for Ad Tech Spring 2026 series:

1. **Audience Segmentation** — Defining target audiences
2. **Identity Graphs** — Cross-device identity resolution
3. **Ad Event Processing** — Impression ingestion, governance, and alerting
4. **Measurement** — Reach, dashboards, and natural-language Q&A on COPPA-filtered exposure logs ← *this project*
