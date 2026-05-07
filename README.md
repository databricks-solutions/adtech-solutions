# Databricks for AdTech Solutions

A collection of Databricks demos, reference architectures, and workshop materials for the AdTech industry — covering data collaboration, AI/BI dashboards, agents, apps + Lakebase, vibe coding, identity graphs, ad event processing, and measurement.

## What's here

The repo is organized by **series**. Each series is a workshop run delivered for AdTech customers; each session within a series stands on its own.

### [`adtech_series_fa25/`](./adtech_series_fa25/) — Fall 2025
Five-session virtual series (Sept 10–25, 2025) covering:
1. Data Collaboration for AdTech (Delta Sharing, Clean Rooms, Marketplace)
2. AI/BI and Genie
3. Agents for AdTech (Knowledge Assistant + policy pack)
4. Databricks Apps & Lakebase (multi-agent chat app, the flagship deliverable)
5. Databricks Development Starter Kit (vibe coding)

See the [series README](./adtech_series_fa25/README.md) for the full session index and per-folder summaries.

### [`adtech_series_sp26/`](./adtech_series_sp26/) — Spring 2026
Four-session series covering:
1. Audience Segmentation
2. Identity Graphs
3. Ad Event Processing (impression ingestion, PII governance, frequency-cap alerting, real-time pacing)
4. Measurement

See the [series README](./adtech_series_sp26/README.md) for details.

## Who this is for

- Databricks Field Engineering (SAs / DSAs) prepping or running AdTech customer enablement
- AdTech customers exploring Databricks reference patterns
- Anyone wanting working examples of these patterns on Databricks

## Repository conventions

- Each series folder has its own `README.md` with session summaries and pointers to per-session content.
- Empty session folders (with `.gitkeep`) are intentional placeholders for sessions whose materials haven't been published yet — kept so paths and the session index stay stable.
- Sample data shared across multiple sessions in a series lives under that series' `shared/` (e.g. [`adtech_series_fa25/shared/megacorp_data/`](./adtech_series_fa25/shared/megacorp_data/)).
- Anything outside a series folder is general AdTech content not tied to a single workshop.

## Contributing

Open a PR. Keep new content within the existing series folder if it's session-specific, or under that series' `shared/` if it's cross-session. New series get their own top-level folder following the `adtech_series_<term>/` naming.

## Support disclaimer

The content here is for reference and educational use only — not officially supported by Databricks under any SLAs. All materials are provided AS IS, without guarantees, and are not intended for production use without proper review and testing.

Source code is provided under the Databricks License. All included or referenced third-party libraries are subject to their respective licenses.

If you hit issues, please open a [GitHub Issue](https://github.com/databricks-solutions/adtech-solutions/issues). Reviewed as time permits — there are no formal SLAs.

## License

&copy; 2025 Databricks, Inc. All rights reserved. The source in this repo is provided subject to the [Databricks License](https://databricks.com/db-license-source). All included or referenced third-party libraries are subject to the licenses set forth below.
