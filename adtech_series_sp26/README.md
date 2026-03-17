# Databricks for Ad Tech — Ad Event Processing

Session 3 of the Databricks for Ad Tech Spring 2026 series. Builds a complete impression event processing pipeline — from raw ingestion with PII governance to frequency cap alerting and real-time campaign pacing.

## Overview

MegaCorp, a fictional media conglomerate, runs 7 ad campaigns across CTV, mobile, and web. Each campaign has a contractual frequency cap and a target frequency. This project demonstrates how to ingest billions of impression events, enforce schema discipline at the source, govern PII from day one, and alert on frequency cap violations within minutes — all on Databricks.

This session sits between **Identity Graphs** (Session 2) and **Measurement** (Session 4). The clean, governed exposure logs produced here feed directly into the measurement dashboards built in Session 4.

## Architecture

### 1. Batch Streaming Pipeline (Spark Declarative Pipelines)

```
Ad Server Beacons
    → Bronze: raw_impression_logs (append-only, schema-enforced, PII masked)
        → Silver: megacorp_impressions (daily user-grain aggregation, 2-hr watermark)
            → Gold: megacorp_user_frequency (lifetime frequency per user per campaign)
                → SQL Alert: frequency cap violation check every 15 minutes
```

- **Bronze** — Compliance layer. Accepts raw events, enforces schema on write, applies Unity Catalog column masks (`mask_ip_address`, `generalize_zip`) to PII columns. Change Data Feed enabled for downstream streaming.
- **Silver** — Measurement layer. Flattens nested structs, derives device type (CTV/Mobile/Web) from IFA, classifies identity status (matched/unmatched), aggregates to daily user-grain with a 2-hour watermark for late arrivals.
- **Gold** — Operations layer. Materialized view of lifetime impression frequency per user per campaign (matched identities only). Powers the frequency cap alert.

### 2. Real-Time Pipeline (Kafka + Spark RTM + Lakebase + Databricks App)

```
Ad Server → Kafka (Avro) → Spark Structured Streaming (Real-Time Mode)
    → Lakebase (managed PostgreSQL) → Campaign Pacing App (FastAPI + React)
```

Sub-second processing for live campaign pacing. The React dashboard polls Lakebase every 2 seconds, showing impressions delivered, spend against budget, and pacing status (Active / Pacing Fast / Stopped).

## Project Structure

```
adtech_series_sp26/
├── impression_logs/                    # Batch streaming DAB
│   ├── databricks.yml                  # Bundle config (catalog, schema, workspace)
│   ├── resources/
│   │   ├── impression_logs_pipeline.yml  # SDP pipeline (serverless + Photon)
│   │   ├── impression_logs_trigger_job.yml  # Trigger job (fires on bronze update)
│   │   ├── bronze_table_setup_job.yml    # Job to create bronze table + masks
│   │   ├── frequency_cap_setup_job.yml   # Job to create/populate frequency caps table
│   │   └── frequency_cap_alert.yml       # SQL alert (every 15 min)
│   └── src/
│       ├── bronze_table_setup/setup.py   # Bronze DDL + column masks
│       ├── frequency_cap_setup/setup.py  # Frequency caps reference data
│       └── impression_logs_transforms/
│           └── transforms.py             # SDP pipeline (bronze → silver → gold)
├── impression_logs_realtime/           # Real-time streaming DAB
│   ├── databricks.yml
│   ├── resources/
│   │   ├── kafka_producer_job.yml        # Kafka event generator
│   │   ├── campaign_pacing_job.yml       # Spark RTM pacing consumer
│   │   ├── lakebase.yml                  # Lakebase instance config
│   │   └── campaign_pacing_app.yml       # Databricks App resource
│   ├── src/
│   │   ├── kafka_producer/generator.py   # Generates impression events to Kafka
│   │   └── campaign_pacing/pacing_consumer.py  # Spark RTM → Lakebase
│   ├── campaign_pacing_app/            # Databricks App (FastAPI + React)
│   │   ├── app.yaml
│   │   ├── src/                        # FastAPI backend
│   │   └── frontend/                   # React + Tailwind dashboard
│   └── scripts/deploy.sh
├── identity_graph/                     # (Session 2 — placeholder)
├── segment_builder/                    # (Session 1 — placeholder)
└── measurement/                        # (Session 4 — placeholder)
```

## Databricks Features Demonstrated

| Feature | Where Used |
|---|---|
| Spark Declarative Pipelines (SDP) | `impression_logs/src/.../transforms.py` — Bronze → Silver → Gold |
| Unity Catalog Column Masks | `bronze_table_setup/setup.py` — `mask_ip_address`, `generalize_zip` |
| Delta Change Data Feed | Bronze table property — powers SDP streaming reads |
| Schema Enforcement | Bronze table — `CREATE TABLE` with typed columns |
| Watermarking | Silver aggregation — 2-hour watermark for late arrivals |
| SQL Alerts | `frequency_cap_alert.yml` — 15-min cron, threshold-based |
| Databricks Asset Bundles | Both `impression_logs/` and `impression_logs_realtime/` are DABs |
| Serverless + Photon | SDP pipeline runs serverless with Photon enabled |
| Spark Real-Time Mode | `pacing_consumer.py` — sub-second stateful streaming |
| Lakebase (Managed PostgreSQL) | `lakebase.yml` — low-latency serving layer for pacing data |
| Databricks Apps | `campaign_pacing_app/` — FastAPI + React deployed as a Databricks App |
| Kafka Integration | Producer generates Avro events; consumer reads via Spark |

## Prerequisites

- Databricks workspace with Unity Catalog enabled
- Databricks CLI configured and authenticated
- Python 3.10+
- Node.js 18+ (for the campaign pacing app frontend)
- Access to Amazon MSK / Kafka (for the real-time pipeline)

## Deployment

### Batch Pipeline

```bash
cd impression_logs
databricks bundle deploy -t dev
databricks bundle run bronze_table_setup -t dev    # Create bronze table + masks
databricks bundle run frequency_cap_setup -t dev   # Populate frequency caps
databricks bundle run impression_logs_dlt -t dev   # Run the SDP pipeline
```

### Real-Time Pipeline

```bash
cd impression_logs_realtime
databricks bundle deploy -t dev
# See scripts/deploy.sh for the full orchestrated deployment
```

## Series Context

This is **Session 3 of 4** in the Databricks for Ad Tech Spring 2026 series:

1. **Audience Segmentation** — Defining target audiences (Amelia Chu, David)
2. **Identity Graphs** — Cross-device identity resolution (Ryan)
3. **Ad Event Processing** — Impression ingestion, governance, and alerting (Tanner Wendland) ← *this repo*
4. **Measurement** — Dashboards and attribution on clean exposure logs (Megan Tupper, Parth Desai)
