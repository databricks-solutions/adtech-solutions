# CLAUDE.md — Impression Logs Realtime Demo

## JDBC Streaming Sink (PrPr) — Lakebase with Real-Time Mode

Source doc: https://docs.google.com/document/d/11t325z8fMR7WoWJqy4RmqKwMmaIHgmKSPs7dqZBBTG4/edit
Go-link: `go/streaming-jdbc-prpr`
PM: Navneeth Nair | Tech Lead: Jerry Peng | Eng: Chloe Xia

### Prerequisites

- **Feature flag** (required spark config on the cluster):
  ```
  spark.sql.streaming.jdbc.enabled = true
  ```
- **Dedicated (assigned) cluster only** — serverless not supported in PrPr.
- **Target table must pre-exist** — the sink does not auto-create tables.
- The upsert key column(s) must have a `PRIMARY KEY` or `UNIQUE` constraint on the table.

### API

```python
df.writeStream \
  .format("jdbcStreaming") \
  .option(...)
  .outputMode("update") \
  .start()
```

Only `outputMode("update")` is supported. Append is accepted but behaves as upsert.

### Connection Options (mutually exclusive)

**Option A — Lakebase via `instancename` (recommended):**
```python
.option("instancename", "<lakebase-instance-name>")
.option("dbname", "my_database")          # optional, defaults to databricks_postgres
```
Credentials are auto-generated and refreshed each microbatch via the workspace API. Use this for long-running queries — token expiry is handled automatically.

**Option B — Standard JDBC via `url`:**
```python
.option("url", "jdbc:postgresql://host:5432/mydb")
.option("user", dbutils.secrets.get("scope", "pg_user"))
.option("password", dbutils.secrets.get("scope", "pg_pass"))
```
Credentials are NOT auto-refreshed. Lakebase tokens expire in ~1 hour — long-running queries will fail. Use `instancename` for Lakebase.

### All Options

| Option | Required | Default | Description |
|---|---|---|---|
| `instancename` | Yes (if no `url`) | — | Lakebase instance name |
| `url` | Yes (if no `instancename`) | — | JDBC connection URL |
| `dbname` | No | `databricks_postgres` | Database name (only with `instancename`) |
| `user` / `password` | No | — | Used with `url` only |
| `dbtable` | Yes | — | Target table, supports `schema.table` format |
| `upsertkey` | Yes | — | Comma-separated column(s) forming the upsert key |
| `checkpointLocation` | Yes | — | Checkpoint directory path |
| `batchsize` | No | 1000 | Max rows per DB transaction |
| `batchinterval` | No | not set | Max buffer dwell time before flush — **set this for RTM** (e.g., `"50 milliseconds"`) |

### Batching Behavior

A flush triggers when either:
- Buffer reaches `batchsize` rows, OR
- Buffer age exceeds `batchinterval`

If `batchinterval` is not set, low-throughput streams may hold rows in the buffer for extended periods. **Always set `batchinterval` when using Real-Time Mode.**

### Connection Behavior

- No connection pooling — each sink partition maintains its own dedicated DB connection.
- **Limit shuffle partitions to ~10** to avoid overwhelming Lakebase's connection limit.
- Transient errors (connection failures, deadlocks, rate limiting) are retried with exponential backoff.
- Known error under load: `FATAL: Connection attempt rate limit exceeded` — this is auto-retried. Fix merged in DBR ~18.0/18.1.

### Upsert Behavior

Uses PostgreSQL's upsert syntax:
```sql
INSERT INTO table (...) ON CONFLICT (upsert_key) DO UPDATE SET ...
```

### Example — Lakebase with RTM

```python
spark.conf.set("spark.sql.streaming.jdbc.enabled", "true")

df.writeStream \
  .format("jdbcStreaming") \
  .option("instancename", "<lakebase-instance-name>") \
  .option("dbname", "my_database") \
  .option("dbtable", "my_schema.my_table") \
  .option("upsertkey", "id") \
  .option("batchinterval", "50 milliseconds") \
  .option("checkpointLocation", "/checkpoints/my_query") \
  .outputMode("update") \
  .trigger(realTime="5 minutes") \
  .start()
```

### What's Supported

| Trigger | Supported |
|---|---|
| Real-Time Mode | Yes |
| ProcessingTime | Yes |
| AvailableNow | Yes |
| Once | Yes |

| Language | Supported |
|---|---|
| Python | Yes |
| Scala | Yes |

| Database | Supported |
|---|---|
| Lakebase | Yes |
| External PostgreSQL | Yes |
| SQL Server, MySQL, etc. | No (future) |

### Future Work (post-PrPr)

- Serverless (SDP) support
- Auto-create table if not exists
- Auto-infer upsert key from primary key
- Additional databases (SQL Server, etc.)
- True append (insert-only) output mode
- Connector renamed from `jdbcStreaming` → `jdbc` to align with batch JDBC connector
