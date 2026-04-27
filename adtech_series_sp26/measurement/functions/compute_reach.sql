-- UC Function: compute_reach
-- Feature: AdTech Series Measurement Demo
--
-- Purpose: Encode the advertiser's individual reach definition in a single,
--          catalogued location so every tool (dashboard, Genie, notebooks)
--          calls the same formula.
--
--   Reads rollup rows from reach_cube using the 'All' sentinel:
--     No-filter call  → publisher = 'All', content = 'All', ... (campaign-total rollup row)
--     Filtered call   → publisher = p_publisher, content = 'All', ... (single-dim rollup row)
--
-- Prerequisites:
--   media_advertising.gold.reach_cube must exist with rollup rows (created by pipeline).
--   reach_totals was removed in Phase 11 — do not reference it.

CREATE OR REPLACE FUNCTION media_advertising.gold.compute_reach(
  p_campaign   STRING   COMMENT 'Campaign name to query reach for. Required.',
  p_publisher  STRING   DEFAULT NULL COMMENT 'Optional: filter to a specific publisher.',
  p_content    STRING   DEFAULT NULL COMMENT 'Optional: filter to a specific content title.'
)
RETURNS BIGINT
COMMENT 'Returns the count of distinct individuals (individual reach) exposed to a campaign. \
COPPA-filtered and deduplicated by mc_indid (megacorp_indid). \
Reads rollup rows from reach_cube: campaign-total row (all dims = ''All'') for no-filter calls, \
single-dimension rollup rows for filtered calls. \
NULL optional parameters mean "all values" — the corresponding dim is matched as ''All''.'
RETURN (
  SELECT COALESCE(SUM(reach_ind), 0)
  FROM   media_advertising.gold.reach_cube
  WHERE  campaign         = p_campaign
    AND  publisher        = COALESCE(p_publisher, 'All')
    AND  content          = COALESCE(p_content,   'All')
    AND  device_type      = 'All'
    AND  inventory_type   = 'All'
    AND  marketing_region = 'All'
);

-- ── Usage examples ────────────────────────────────────────────────────────────

-- Total individual reach for a campaign (campaign-total rollup row)
-- SELECT media_advertising.gold.compute_reach('Terrific Tacos');
-- → 696,592

-- Reach for a specific publisher (publisher rollup row)
-- SELECT media_advertising.gold.compute_reach('Terrific Tacos', 'Big Mountain');

-- Reach for a specific content title (content rollup row)
-- SELECT media_advertising.gold.compute_reach('Terrific Tacos', NULL, 'Frasier');

-- Reach for a specific publisher + content (no matching rollup row → returns 0 or partial)
-- Note: combine publisher + content filtering requires detail-row query, not this function
-- SELECT media_advertising.gold.compute_reach('Terrific Tacos', 'Rainbow Hemisphere', 'Frasier');

-- Consistency check: function vs rollup row direct query (SC-004)
-- SELECT
--   media_advertising.gold.compute_reach('Terrific Tacos', 'Big Mountain') AS fn_reach,
--   reach_ind AS cube_reach
-- FROM media_advertising.gold.reach_cube
-- WHERE campaign = 'Terrific Tacos' AND publisher = 'Big Mountain'
--   AND device_type = 'All' AND inventory_type = 'All'
--   AND content = 'All' AND marketing_region = 'All';
-- fn_reach MUST equal cube_reach
