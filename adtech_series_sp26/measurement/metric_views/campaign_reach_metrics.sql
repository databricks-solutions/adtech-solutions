-- Metric View: campaign_reach_metrics
-- Feature: AdTech Series Measurement Demo
--
-- Purpose: Expose reach_individual as a governed, queryable metric layer that
--          AI/BI Genie and dashboards consume natively.
--          Defines the business vocabulary: six dimensions and six measures.
--
-- Prerequisites: media_advertising.gold.reach_cube must exist (created by pipeline).
-- Runtime requirement: DBR 17.2+ (for YAML version 1.1).

CREATE OR REPLACE VIEW media_advertising.gold.campaign_reach_metrics
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Campaign reach KPIs: COPPA-filtered, deduplicated reach metrics across six
    dimensions (Campaign, Publisher, Device Type, Inventory Type, Content, Marketing Region)
    and six measures (Individual Reach, Household Reach, IP Reach, Email Reach,
    Total Matched Impressions, Total Raw Impressions).
    Source: media_advertising.gold.reach_individual (individual-level gold table, built by the reach pipeline).
    Do not modify dimension/measure names — Genie space configuration depends on them."
  source: media_advertising.gold.reach_individual

  dimensions:
    - name: Campaign
      expr: campaign
      comment: "Advertising campaign name (e.g. 'Terrific Tacos', 'Happy Dogs')"

    - name: Publisher
      expr: publisher
      comment: "Distribution platform that served the ad"

    - name: Device Type
      expr: device_type
      comment: "Device environment: CTV, Mobile, or Web — derived from IFA prefix in request_kv._server_ifa"

    - name: Inventory Type
      expr: inventory_type
      comment: "Ad buying channel: CTV (premium/guaranteed deals), Mobile, or Other (open/standard) — derived from IFA prefix"

    - name: Content
      expr: content
      comment: "Title of the content in which the ad appeared"

    - name: Marketing Region
      expr: marketing_region
      comment: "Named US advertising market derived from ZIP code prefix via zip3_marketing_region lookup table"

  measures:
    - name: Individual Reach
      expr: COUNT(DISTINCT mc_indid)
      comment: "Count of distinct individuals reached (COPPA-filtered, deduplicated by mc_indid). Correct at any query grain — no double-counting across dimension combinations."

    - name: Household Reach
      expr: COUNT(DISTINCT hhid)
      comment: "Count of distinct households reached (deduplicated by megacorp_hhid from the campaign audience list). Correct at any query grain."

    - name: IP Reach
      expr: COUNT(DISTINCT ip_address)
      comment: "Count of distinct IP addresses reached across the campaign audience. Correct at any query grain."

    - name: Email Reach
      expr: COUNT(DISTINCT server_email)
      comment: "Count of distinct email addresses reached (sourced from request_kv._server_email). Correct at any query grain."

    - name: Total Matched Impressions
      expr: SUM(imps)
      comment: "Impressions surviving COPPA exclusion AND matched to the campaign audience via INNER JOIN."

    - name: Total Raw Impressions
      expr: SUM(raw_imps_kpi)
      comment: "All impressions before any filtering — total raw inventory served for this campaign. raw_imps_kpi is additive at any query grain via ROW_NUMBER attribution in reach_individual."
$$;

-- ── Sample queries ────────────────────────────────────────────────────────────

-- Individual reach by publisher for a campaign
-- SELECT
--   `Publisher`,
--   MEASURE(`Individual Reach`)          AS reach_ind,
--   MEASURE(`Household Reach`)           AS reach_hhid,
--   MEASURE(`Total Matched Impressions`) AS matched_imps
-- FROM media_advertising.gold.campaign_reach_metrics
-- WHERE `Campaign` = 'Terrific Tacos'
-- GROUP BY ALL
-- ORDER BY reach_ind DESC;

-- Reach by device type (CTV vs Mobile vs Web)
-- SELECT
--   `Device Type`,
--   MEASURE(`Individual Reach`) AS reach
-- FROM media_advertising.gold.campaign_reach_metrics
-- WHERE `Campaign` = 'Terrific Tacos'
-- GROUP BY ALL
-- ORDER BY reach DESC;

-- Reach by inventory type (CTV premium vs Mobile vs Other open)
-- SELECT
--   `Inventory Type`,
--   MEASURE(`Individual Reach`) AS reach
-- FROM media_advertising.gold.campaign_reach_metrics
-- WHERE `Campaign` = 'Terrific Tacos'
-- GROUP BY ALL
-- ORDER BY reach DESC;

-- Impression funnel (raw → matched → individual → household)
-- SELECT
--   MEASURE(`Total Raw Impressions`)     AS raw_imps,
--   MEASURE(`Total Matched Impressions`) AS matched_imps,
--   MEASURE(`Individual Reach`)          AS reach_ind,
--   MEASURE(`Household Reach`)           AS reach_hhid
-- FROM media_advertising.gold.campaign_reach_metrics
-- WHERE `Campaign` = 'Terrific Tacos'
-- GROUP BY ALL;

-- Top marketing regions by individual reach
-- SELECT
--   `Marketing Region`,
--   MEASURE(`Individual Reach`) AS reach
-- FROM media_advertising.gold.campaign_reach_metrics
-- WHERE `Campaign` = 'Terrific Tacos'
-- GROUP BY ALL
-- ORDER BY reach DESC
-- LIMIT 10;

-- ── Genie integration note ────────────────────────────────────────────────────
-- When configuring the Genie space:
-- 1. Add campaign_reach_metrics as the dataset
-- 2. Genie maps "Campaign" → "for Terrific Tacos", "for Happy Dogs"
-- 3. Genie maps "Publisher" → "on Big Mountain", "by publisher"
-- 4. Genie maps "Device Type" → "on CTV", "on mobile devices"
-- 5. Genie maps "Inventory Type" → "on premium inventory", "on open inventory"
-- 6. Genie maps "Marketing Region" → "in Los Angeles Metro", "in Chicago Metro"
-- 7. Genie maps "Individual Reach" → "how many people reached", "reach count"
-- 8. MEASURE() wrapper is handled by Genie internally — no manual SQL needed
