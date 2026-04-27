# Quickstart

End-to-end deployment of the AdTech Series Measurement project — pipeline, UC Function, Metric View, dashboard, and Genie space — with verification queries at every step.

Substitute `<warehouse_id>` and `<catalog>` for your workspace's values throughout. The bundle's `catalog` variable defaults to `media_advertising`; override with `--var catalog=<your_catalog>` if different.

All `databricks` CLI commands below assume a profile is configured against your workspace — set `DATABRICKS_CONFIG_PROFILE=<profile>` or pass `--profile <profile>` (omitted in examples for brevity).

## Prerequisites

- Databricks CLI authenticated: `databricks auth login --host <your-workspace-host> --profile <profile>`
- Unity Catalog enabled, with a SQL warehouse accessible to your user
- DBR 17.2+ serverless runtime available (required for Unity Catalog Metric Views)
- Permissions: `CREATE TABLE`, `CREATE FUNCTION`, `CREATE VIEW` on the target catalog's schemas
- Source data in `<catalog>.bronze.impression_logs_prod` and `<catalog>.segments.megacorp_campaigns` (override locations via bundle variables — see `databricks.yml`)
- Python 3.11+ with `databricks-sdk` installed (`pip install databricks-sdk`)

Verify CLI auth:

```bash
databricks auth status
```

## 1. Create the lookup table

ZIP3 → marketing region mapping used by the pipeline.

```bash
databricks sql execute --warehouse-id <warehouse_id> --file tables/zip3_marketing_region.sql
```

Validate:

```sql
SELECT COUNT(*) FROM <catalog>.gold.zip3_marketing_region;
-- Expected: 961

SELECT * FROM <catalog>.gold.zip3_marketing_region WHERE zip3 = '902';
-- Expected: 'Los Angeles Metro'
```

## 2. Create the UC Function

```bash
databricks sql execute --warehouse-id <warehouse_id> --file functions/compute_reach.sql
```

Validation deferred to Step 4 — the function reads from `reach_cube`, which doesn't exist until the pipeline runs.

## 3. Create the Metric View

```bash
databricks sql execute --warehouse-id <warehouse_id> --file metric_views/campaign_reach_metrics.sql
```

Validation deferred to Step 4 — the view reads from `reach_individual`, which doesn't exist until the pipeline runs.

## 4. Deploy and run the bundle

The bundle deploys the pipeline and the dashboard together. Running the pipeline performs a full refresh of all silver and gold reach tables.

```bash
databricks bundle deploy --var warehouse_id=<warehouse_id>
databricks bundle run reach_pipeline
```

Tables produced:

| Table | Purpose |
|---|---|
| `<catalog>.silver.reach_impressions` | Individual-level daily aggregation |
| `<catalog>.silver.reach_prelim` | Campaign-level identity-string aggregation |
| `<catalog>.gold.reach_cube` | Detail rows + 12 rollup levels (powers the cube-based dashboard widgets and `compute_reach`) |
| `<catalog>.gold.reach_individual` | Individual-level rows; source for the Metric View |

Validate the pipeline output:

```sql
-- reach_cube populated
SELECT COUNT(*) FROM <catalog>.gold.reach_cube;
-- Expected: > 0

-- Funnel invariant: raw_imps must always be >= matched_imps
SELECT COUNT(*) AS violations
FROM <catalog>.gold.reach_cube
WHERE raw_imps < matched_imps;
-- Expected: 0

-- Marketing region populated for every row
SELECT COUNT(*) FROM <catalog>.gold.reach_cube WHERE marketing_region IS NULL;
-- Expected: 0

-- Device type breakdown — sample data has 3 values
SELECT DISTINCT device_type FROM <catalog>.gold.reach_cube;
-- Expected: CTV, Mobile, Web
```

Validate the UC Function:

```sql
-- Returns the campaign-total rollup row's reach_ind
SELECT <catalog>.gold.compute_reach('Terrific Tacos');
-- Expected: a non-zero number

-- Function output must equal a direct read of the same rollup row
SELECT
  <catalog>.gold.compute_reach('Terrific Tacos', 'Big Mountain') AS fn_reach,
  reach_ind                                                       AS cube_reach
FROM <catalog>.gold.reach_cube
WHERE campaign         = 'Terrific Tacos'
  AND publisher        = 'Big Mountain'
  AND device_type      = 'All'
  AND inventory_type   = 'All'
  AND content          = 'All'
  AND marketing_region = 'All';
-- fn_reach must equal cube_reach
```

Validate the Metric View:

```sql
SELECT
  `Device Type`,
  MEASURE(`Individual Reach`)          AS reach_ind,
  MEASURE(`Household Reach`)           AS reach_hhid,
  MEASURE(`IP Reach`)                  AS reach_ip,
  MEASURE(`Email Reach`)               AS reach_email,
  MEASURE(`Total Matched Impressions`) AS matched_imps,
  MEASURE(`Total Raw Impressions`)     AS raw_imps
FROM <catalog>.gold.campaign_reach_metrics
WHERE `Campaign` = 'Terrific Tacos'
GROUP BY ALL
ORDER BY reach_ind DESC;
-- Expected: one row per device_type, all six measures non-zero
```

Validate the dashboard: open the URL printed by `bundle deploy` and confirm widgets populate. The dashboard is two pages:

- **Campaign Overview** — 6 KPI counters (raw → matched → individual → household → IP → email reach), reach-by-publisher / device-type / inventory / content / region charts, and a campaign → publisher → device-type Sankey
- **Dimension Explorer** — table of all dimension combinations with 6 filters

## 5. Create the Genie space

The space `AdTech Series — Campaign Reach Q&A` provides natural-language access to the reach data. Its full definition (instructions, SQL examples, benchmarks) lives at `genie_spaces/campaign_reach_qa.json`. The committed JSON has `space_id: null`; populate it after the first deploy if you want a reproducible round-trip.

### Fresh create (first deploy in any workspace)

```bash
python genie_spaces/deploy_genie_space.py \
  --parent-path "/Shared/Adtech-measurement" \
  --warehouse-id <warehouse_id>
```

Outputs the new `space_id` and URL. Paste the `space_id` into `genie_spaces/campaign_reach_qa.json` and commit if you want subsequent runs to default to it.

### Update an existing space

```bash
python genie_spaces/deploy_genie_space.py \
  --space-id <space_id> \
  --warehouse-id <warehouse_id>
```

### Deploy to a different catalog/schema

The deploy script rewrites every `media_advertising.gold` reference in the space config to your target.

```bash
python genie_spaces/deploy_genie_space.py \
  --catalog <catalog> --schema <schema> \
  --warehouse-id <warehouse_id> \
  --parent-path "/Shared/Adtech-measurement"
```

### Pull latest space back to the repo (after edits in the UI)

```bash
SPACE_ID=$(python3 -c "import json; print(json.load(open('genie_spaces/campaign_reach_qa.json')).get('space_id') or '')")
[ -z "$SPACE_ID" ] && { echo "space_id not set in campaign_reach_qa.json"; exit 1; }
databricks api get "/api/2.0/genie/spaces/${SPACE_ID}?include_serialized_space=true" | python3 -c "
import json, sys
data = json.load(sys.stdin)
data['serialized_space'] = json.loads(data['serialized_space'])
data.pop('parent_path', None)  # workspace path — not needed for deploy
with open('genie_spaces/campaign_reach_qa.json', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write('\n')
print('Saved to genie_spaces/campaign_reach_qa.json')
"
```

### Run the routing eval

```bash
python genie_spaces/eval_genie_space.py --space-id <space_id> --warehouse-id <warehouse_id>
# Expected: 11/11 passed
```

The eval covers:

- Cross-dimensional reach breakdowns (must use the Metric View — `reach_cube` rollups only collapse one dimension at a time)
- Single-dimension reach (Metric View)
- Campaign-total reach (either source acceptable)
- Raw vs matched impression comparisons (must use `reach_cube` — only source for `raw_imps`)

## Genie Space — Data Sources & Routing

The space's instructions encode TABLE ROUTING rules:

- `<catalog>.gold.campaign_reach_metrics` (Metric View) — primary source for any reach question. Use `MEASURE()` syntax; correct deduplication at any grain.
- `<catalog>.gold.reach_cube` (Table) — only source for `raw_imps`. Detail + rollup rows.

Cross-dimensional breakdowns (e.g., publisher × device_type, campaign × publisher) must use the Metric View — `reach_cube` rollup rows only collapse one dimension at a time.
