# Databricks notebook source
# MAGIC %md
# MAGIC # Frequency Cap Reference Table Setup
# MAGIC
# MAGIC This notebook creates and populates the campaign frequency cap reference table.
# MAGIC The alert system joins this table against the gold user frequency table
# MAGIC to detect users who have been over-served beyond their campaign's cap.
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS ${catalog}.gold.campaign_frequency_caps (
# MAGIC   campaign_name STRING NOT NULL,
# MAGIC   frequency_cap INT NOT NULL,
# MAGIC   in_target_freq INT NOT NULL,
# MAGIC   pct_pop DOUBLE NOT NULL
# MAGIC )
# MAGIC USING DELTA
# MAGIC TBLPROPERTIES ('quality' = 'reference');

# COMMAND ----------

# MAGIC %md
# MAGIC ## Upsert Campaign Frequency Caps

# COMMAND ----------

# MAGIC %sql
# MAGIC MERGE INTO ${catalog}.gold.campaign_frequency_caps AS target
# MAGIC USING (
# MAGIC   SELECT col1 AS campaign_name, col2 AS frequency_cap, col3 AS in_target_freq, col4 AS pct_pop
# MAGIC   FROM VALUES
# MAGIC     ('Happy Dogs',      10, 5,  0.60),
# MAGIC     ('Terrific Tacos',  15, 5,  0.25),
# MAGIC     ('Best Burgers',    10, 5,  0.30),
# MAGIC     ('Cool Car',        15, 5,  0.10),
# MAGIC     ('Super Savings',   25, 10, 0.05),
# MAGIC     ('Fresh Flowers',   30, 6,  0.05),
# MAGIC     ('Moving Movie',     5, 9,  0.10)
# MAGIC ) AS source
# MAGIC ON target.campaign_name = source.campaign_name
# MAGIC WHEN MATCHED THEN UPDATE SET *
# MAGIC WHEN NOT MATCHED THEN INSERT *;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Setup

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM ${catalog}.gold.campaign_frequency_caps ORDER BY frequency_cap;
