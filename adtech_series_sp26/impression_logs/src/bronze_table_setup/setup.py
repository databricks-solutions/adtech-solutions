# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Table Setup
# MAGIC
# MAGIC This notebook sets up the bronze table with:
# MAGIC - Column masking functions for PII protection
# MAGIC - Change Data Feed enabled for downstream DLT consumption

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Masking Functions

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE FUNCTION ${catalog}.bronze.mask_ip_address(ip STRING)
# MAGIC   RETURNS STRING
# MAGIC   LANGUAGE SQL
# MAGIC   DETERMINISTIC
# MAGIC   CONTAINS SQL
# MAGIC   COMMENT 'Masks the last two octets of an IPv4 address for privacy'
# MAGIC   RETURN CASE
# MAGIC     WHEN ip IS NULL THEN NULL
# MAGIC     WHEN ip RLIKE '^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$'
# MAGIC       THEN CONCAT(
# MAGIC         SPLIT(ip, '\\.')[0], '.',
# MAGIC         SPLIT(ip, '\\.')[1], '.xxx.xxx'
# MAGIC       )
# MAGIC     ELSE 'INVALID_IP'
# MAGIC   END;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE FUNCTION ${catalog}.bronze.generalize_zip(zip STRING)
# MAGIC   RETURNS STRING
# MAGIC   LANGUAGE SQL
# MAGIC   DETERMINISTIC
# MAGIC   CONTAINS SQL
# MAGIC   COMMENT 'Generalizes 5-digit zip to 3-digit prefix for k-anonymity'
# MAGIC   RETURN CASE
# MAGIC     WHEN zip IS NULL THEN NULL
# MAGIC     WHEN LENGTH(zip) >= 3 THEN CONCAT(LEFT(zip, 3), 'XX')
# MAGIC     ELSE '[REDACTED]'
# MAGIC   END;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Table

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS ${catalog}.bronze.raw_impression_logs (
# MAGIC   impression_id BIGINT COMMENT 'The unique identifier for the impression activity.',
# MAGIC   date DATE COMMENT 'The date of the impression activity.',
# MAGIC   timestamp TIMESTAMP COMMENT 'The timestamp of the impression activity. This is the timestamp of when the impression activity was recorded by the Ad Server.',
# MAGIC   distributor_name STRING COMMENT 'The name of the distributor that served the impression activity.',
# MAGIC   campaign_name STRING COMMENT 'The name of the campaign of the impression activity.',
# MAGIC   megacorp_indid STRING COMMENT 'The MegaCorp ID of the Consumer as recorded by the Ad Server',
# MAGIC   request_kv STRUCT<_server_email: STRING, _server_ifa: STRING, _is_coppa: BOOLEAN> COMMENT 'The request key-value pairs as recorded by the Ad Server.',
# MAGIC   ip_address STRING COMMENT 'The IP address of the Consumer as recorded by the Ad Server',
# MAGIC   user_zip STRING COMMENT 'The zip code of the Consumer as recorded by the Ad Server',
# MAGIC   user_state STRING COMMENT 'The state of the Consumer as recorded by the Ad Server',
# MAGIC   content_id STRING COMMENT 'The ID of the content that was served as part of the impression',
# MAGIC   content_nm STRING COMMENT 'The name of the content that was served as part of the impression',
# MAGIC   meta_info STRUCT<has_correct_geo: BOOLEAN, has_correct_linkage: BOOLEAN, is_target: BOOLEAN> COMMENT 'The metadata about the impression'
# MAGIC )
# MAGIC USING DELTA;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configure Table

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Enable Change Data Feed for DLT streaming
# MAGIC ALTER TABLE ${catalog}.bronze.raw_impression_logs
# MAGIC   SET TBLPROPERTIES (delta.enableChangeDataFeed = true);

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Apply masking functions to protect sensitive data
# MAGIC ALTER TABLE ${catalog}.bronze.raw_impression_logs
# MAGIC   ALTER COLUMN ip_address SET MASK ${catalog}.bronze.mask_ip_address;

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE ${catalog}.bronze.raw_impression_logs
# MAGIC   ALTER COLUMN user_zip SET MASK ${catalog}.bronze.generalize_zip;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Setup

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE TABLE EXTENDED ${catalog}.bronze.raw_impression_logs;
