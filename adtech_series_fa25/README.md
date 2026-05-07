# Databricks for AdTech — Fall 2025 Series

A five-session virtual workshop series delivered Sept 10–25, 2025 for AdTech customers. Each session is a one-hour talk + demo + Q&A, led by Databricks Solutions Architects.

## Sessions

| # | Date | Session | Folder | Lead(s) |
|---|------|---------|--------|---------|
| 1 | Sept 10 | Data Collaboration for AdTech | [`data_collab/`](./data_collab/) | Amelia Chu |
| 2 | Sept 16 | AI/BI and Genie | [`aibi_genie/`](./aibi_genie/) | Megan Fogal, Sylvia Schumacher |
| 3 | Sept 18 | Agents for AdTech | [`agents/`](./agents/) | Jai Behl |
| 4 | Sept 23 | Databricks Apps & Lakebase | [`app_lakebase/`](./app_lakebase/) | Charlie Hohenstein, Tanner Wendland, David Qiu |
| 5 | Sept 25 | Databricks Development Starter Kit (vibe coding) | [`vibes/`](./vibes/) | David Qiu |

## What's in each session folder

### [`data_collab/`](./data_collab/) — Data Collaboration for AdTech
Picking the right collaboration tool, Delta Sharing, Marketplace, Clean Rooms, taking it to production. *Folder is currently a placeholder — slides only, no code published yet.*

### [`aibi_genie/`](./aibi_genie/) — AI/BI and Genie
- `MegaCorp Campaigns AIBI Demo.lvdash.json` — pre-built Lakeview dashboard for MegaCorp campaign analysis
- `GENIE.md` — Genie space configuration: tables, instructions, example queries

### [`agents/`](./agents/) — Agents for AdTech
- `knowledge_assistant_policies/` — 20-PDF policy pack (data governance, brand voice, regional compliance, accessibility, data dictionaries)
- `custom_llm_creative_examples.csv` — sample creative dataset for LLM-driven campaign generation

### [`app_lakebase/`](./app_lakebase/) — Databricks Apps & Lakebase
The flagship deliverable: a multi-agent chat app (Dash + Postgres + pgvector) with Genie + Knowledge Assistant integration, persistent chat history, and Terraform-managed Lakebase. Full deployment guide in the [folder README](./app_lakebase/README.md).

Also includes [`ad_tech_genie_demo/`](./app_lakebase/ad_tech_genie_demo/) — a separate Streamlit Genie demo by Charlie.

### [`vibes/`](./vibes/) — Databricks Development Starter Kit
Vibe-coding examples: dashboard build walkthrough, sample notebook, Cursor rules, and a small Databricks app scaffold.

## Shared assets

[`shared/megacorp_data/`](./shared/megacorp_data/) — sample datasets used across multiple sessions:
- `megacorp_campaigns.parquet` — campaign-to-individual mappings
- `megacorp_audience_census_profile.parquet` — demographic + behavioral profiles
- `megacorp_segment_definitions.parquet` — segment definitions
- `megacorp_audience_census_profile_metric_view.json` — Unity Catalog metric view definition

## Series narrative

The five sessions build on each other:

1. **Data Collaboration** establishes how data moves between AdTech parties (Delta Sharing, Clean Rooms, Marketplace).
2. **AI/BI & Genie** turns that data into dashboards and natural-language exploration.
3. **Agents** adds policy-aware AI that can reason over campaign content and compliance docs.
4. **Apps & Lakebase** packages those agents into a production-shaped app with persistence.
5. **Vibes** is the meta-session: how to build everything above faster with AI-assisted dev tools.
