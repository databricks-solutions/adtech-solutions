# Data Dictionary: Megacorp Audience Segmentation

This document describes the Databricks Unity Catalog tables used for audience segmentation in the adtech application.

## Table Overview

| Table | Catalog.Schema.Table | Purpose | Row Count |
|-------|---------------------|---------|-----------|
| Audience Profiles | `media_advertising.profiles.megacorp_audience_census_profile` | Individual-level demographic and behavioral attributes | 3,400,000 |
| Campaign Membership | `media_advertising.segments.megacorp_campaigns` | Maps individuals/households to campaigns | 24,650,000 |
| Segment Definitions | `media_advertising.segments.megacorp_segment_definitions` | Segment metadata and targeting rules | 7 |

---

## Entity Relationship Diagram

```
┌─────────────────────────────────┐
│   megacorp_segment_definitions  │
│   (Metadata - 7 rows)           │
├─────────────────────────────────┤
│ segment_name (PK)               │───────┐
│ segment_definition              │       │
│ quarter                         │       │
│ start_date                      │       │ segment_name = campaign_name
│ end_date                        │       │
└─────────────────────────────────┘       │
                                          │
                                          ▼
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│ megacorp_audience_census_profile│     │     megacorp_campaigns          │
│ (Profiles - 3.4M rows)          │     │   (Membership - 24.6M rows)     │
├─────────────────────────────────┤     ├─────────────────────────────────┤
│ megacorp_hhid                   │◄────│ megacorp_hhid                   │
│ megacorp_indid (PK)             │◄────│ megacorp_indid                  │
│ state                           │     │ campaign_name                   │────┘
│ zip5                            │     └─────────────────────────────────┘
│ age                             │
│ gender                          │
│ is_dog_owner                    │
│ is_cat_owner                    │
│ qsr_propensity                  │
│ martial_status                  │
│ income_level                    │
│ education_level                 │
│ is_active_auto_loan             │
│ is_cord_cutter                  │
│ luxury_propensity               │
│ auto_intenders                  │
└─────────────────────────────────┘
```

---

## Table 1: megacorp_audience_census_profile

**Full Path:** `media_advertising.profiles.megacorp_audience_census_profile`

**Purpose:** Core audience data containing demographic attributes and behavioral signals for individuals. This is the primary table for building audience segments based on user characteristics.

**Storage:** Delta format, S3-backed, ~177MB

### Columns

| Column | Type | Nullable | Description | Distinct Values | Null Rate |
|--------|------|----------|-------------|-----------------|-----------|
| `megacorp_hhid` | STRING | Yes | Household identifier - groups individuals by residence | 433,691 | 0% |
| `megacorp_indid` | STRING | Yes | Individual identifier - unique person ID | 3,116,302 | 0% |
| `state` | STRING | Yes | US state code (2-letter) | 57 | 0% |
| `zip5` | STRING | Yes | 5-digit ZIP code | 40,328 | 0% |
| `age` | LONG | Yes | Age in years (18-115) | 91 | 5.0% |
| `gender` | STRING | Yes | Gender classification | 5 | 0% |
| `is_dog_owner` | BOOLEAN | Yes | Dog ownership flag | 2 | 23.0% |
| `is_cat_owner` | BOOLEAN | Yes | Cat ownership flag | 1 | 57.0% |
| `qsr_propensity` | STRING | Yes | Quick-service restaurant propensity score | 4 | 31.0% |
| `martial_status` | STRING | Yes | Marital status (note: typo in source) | 5 | 0% |
| `income_level` | STRING | Yes | Income bracket/level | 4,226 | 0% |
| `education_level` | STRING | Yes | Highest education attained | 4 | 0% |
| `is_active_auto_loan` | BOOLEAN | Yes | Currently has auto loan | 2 | 7.0% |
| `is_cord_cutter` | BOOLEAN | Yes | No traditional cable subscription | 1 | 46.0% |
| `luxury_propensity` | STRING | Yes | Luxury goods purchase propensity | 6 | 31.0% |
| `auto_intenders` | BOOLEAN | Yes | In-market for vehicle purchase | 2 | 15.0% |

### Key Insights

- **Household vs Individual:** ~433K households contain ~3.1M individuals (avg ~7.8 individuals per household)
- **Geographic Coverage:** 57 state codes (includes territories), 40K+ ZIP codes
- **Age Distribution:** Adults only (18+), up to 115 years old
- **Data Sparsity:** Several behavioral flags have significant null rates (30-57%), indicating partial coverage from data providers

### Common Query Patterns

```sql
-- Get profile for specific individual
SELECT * FROM media_advertising.profiles.megacorp_audience_census_profile
WHERE megacorp_indid = 'xxx';

-- Aggregate by household
SELECT megacorp_hhid, COUNT(*) as household_size
FROM media_advertising.profiles.megacorp_audience_census_profile
GROUP BY megacorp_hhid;

-- Filter by demographic criteria
SELECT * FROM media_advertising.profiles.megacorp_audience_census_profile
WHERE age BETWEEN 25 AND 54
  AND income_level IN ('$100K-$150K', '$150K+')
  AND is_dog_owner = true;
```

---

## Table 2: megacorp_campaigns

**Full Path:** `media_advertising.segments.megacorp_campaigns`

**Purpose:** Junction table mapping individuals and households to campaign segments. Each row represents membership in a specific campaign. One individual can belong to multiple campaigns.

**Storage:** Delta format, S3-backed, ~1.1GB

### Columns

| Column | Type | Nullable | Description | Distinct Values |
|--------|------|----------|-------------|-----------------|
| `megacorp_indid` | STRING | Yes | Individual identifier - FK to profiles | 1,433,140 |
| `megacorp_hhid` | STRING | Yes | Household identifier - FK to profiles | 489,366 |
| `campaign_name` | STRING | Yes | Campaign/segment name - FK to definitions | 6 |

### Key Insights

- **Many-to-Many Relationship:** 24.6M rows for 1.4M unique individuals = avg ~17 campaign memberships per person
- **Campaign Count:** 6 distinct campaigns defined
- **Coverage:** ~42% of individuals in profiles (1.4M / 3.4M) are in at least one campaign
- **Household Overlap:** 489K households (vs 433K in profiles) - some campaigns may include households not fully represented in profiles

### Campaign Membership Distribution

```sql
-- Count members per campaign
SELECT campaign_name,
       COUNT(DISTINCT megacorp_indid) as unique_individuals,
       COUNT(DISTINCT megacorp_hhid) as unique_households
FROM media_advertising.segments.megacorp_campaigns
GROUP BY campaign_name;

-- Find individuals in multiple campaigns
SELECT megacorp_indid, COUNT(DISTINCT campaign_name) as campaign_count
FROM media_advertising.segments.megacorp_campaigns
GROUP BY megacorp_indid
HAVING COUNT(DISTINCT campaign_name) > 1;
```

---

## Table 3: megacorp_segment_definitions

**Full Path:** `media_advertising.segments.megacorp_segment_definitions`

**Purpose:** Metadata table containing segment/campaign definitions, targeting criteria, and scheduling information. Used to understand what each segment represents and when it's active.

**Storage:** Delta format, S3-backed, ~2.6KB

### Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `segment_name` | STRING | Yes | Segment identifier - matches campaign_name in campaigns table |
| `segment_definition` | STRING | Yes | Human-readable targeting criteria/rules (up to 148 chars) |
| `quarter` | STRING | Yes | Fiscal quarter (e.g., "Q1") |
| `start_date` | DATE | Yes | Campaign start date |
| `end_date` | DATE | Yes | Campaign end date |

### Key Insights

- **7 Segment Definitions:** One more than the 6 campaign_names in campaigns table (likely includes a deprecated or planned segment)
- **Q1 2026 Campaign:** All segments run Jan 1 - Mar 30, 2026
- **Definition Length:** Avg 130 characters - detailed targeting criteria

### Expected Segment Types

Based on the profile attributes, likely segments include:
- **Pet Owners:** Dog/cat ownership targeting
- **Auto Intenders:** In-market vehicle buyers
- **Cord Cutters:** Streaming-first audiences
- **Income Tiers:** Affluent/luxury propensity
- **QSR Enthusiasts:** Fast food propensity
- **Geographic:** State/regional targeting

```sql
-- View all segment definitions
SELECT * FROM media_advertising.segments.megacorp_segment_definitions
ORDER BY segment_name;

-- Find active segments for a date
SELECT * FROM media_advertising.segments.megacorp_segment_definitions
WHERE start_date <= CURRENT_DATE() AND end_date >= CURRENT_DATE();
```

---

## Table Relationships

### Join Keys

| Relationship | Join Condition | Cardinality |
|--------------|----------------|-------------|
| Profiles ↔ Campaigns | `profiles.megacorp_indid = campaigns.megacorp_indid` | 1:N |
| Profiles ↔ Campaigns | `profiles.megacorp_hhid = campaigns.megacorp_hhid` | 1:N |
| Campaigns ↔ Definitions | `campaigns.campaign_name = definitions.segment_name` | N:1 |

### Common Join Patterns

```sql
-- Get campaign members with their profile attributes
SELECT
    c.campaign_name,
    p.megacorp_indid,
    p.age,
    p.gender,
    p.income_level,
    p.state
FROM media_advertising.segments.megacorp_campaigns c
JOIN media_advertising.profiles.megacorp_audience_census_profile p
    ON c.megacorp_indid = p.megacorp_indid
WHERE c.campaign_name = 'target_segment';

-- Get full campaign details with definitions
SELECT
    d.segment_name,
    d.segment_definition,
    d.start_date,
    d.end_date,
    COUNT(DISTINCT c.megacorp_indid) as member_count
FROM media_advertising.segments.megacorp_segment_definitions d
LEFT JOIN media_advertising.segments.megacorp_campaigns c
    ON d.segment_name = c.campaign_name
GROUP BY d.segment_name, d.segment_definition, d.start_date, d.end_date;

-- Analyze segment overlap
SELECT
    c1.campaign_name as segment_1,
    c2.campaign_name as segment_2,
    COUNT(DISTINCT c1.megacorp_indid) as overlap_count
FROM media_advertising.segments.megacorp_campaigns c1
JOIN media_advertising.segments.megacorp_campaigns c2
    ON c1.megacorp_indid = c2.megacorp_indid
    AND c1.campaign_name < c2.campaign_name
GROUP BY c1.campaign_name, c2.campaign_name
ORDER BY overlap_count DESC;
```

---

## Data Quality Notes

### Known Issues

1. **Typo in Column Name:** `martial_status` should be `marital_status`
2. **Sparse Behavioral Data:** Several boolean flags have 30-60% null rates
3. **is_cat_owner Anomaly:** Only 1 distinct value (false) with 57% nulls - likely data quality issue

### Recommendations

1. **Handle Nulls:** Treat null behavioral flags as "unknown" rather than false
2. **Validate Joins:** Not all campaign members may have profile data (489K HH in campaigns vs 433K in profiles)
3. **Date Filtering:** Always filter by segment date range for time-sensitive queries

---

## Access Information

| Property | Value |
|----------|-------|
| Catalog | `media_advertising` |
| Metastore ID | `b169b504-4c54-49f2-bc3a-adf4b128f36d` |
| Storage | S3 (`s3://databricks-e2demofieldengwest/...`) |
| Format | Delta |
| Owner | amelia.chu@databricks.com |
| Last Updated | January 2026 |
