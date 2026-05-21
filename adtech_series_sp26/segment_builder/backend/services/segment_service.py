"""Business logic for segment operations."""

import logging
import time
import uuid
from datetime import date

from backend.config.table_overrides import (
    get_campaigns_table,
    get_definitions_table,
    get_profiles_table,
)
from backend.config.column_overrides import (
    get_campaigns_identity_household_column,
    get_campaigns_identity_individual_column,
    get_campaigns_segment_name_column,
    get_profile_identity_household_column,
    get_profile_identity_individual_column,
)
from backend.models.segment import (
    SegmentBuildResponse,
    SegmentDefinition,
    SegmentPreviewResponse,
)
from backend.services.databricks_client import get_databricks_client
from backend.services.sql_generator import get_sql_generator

logger = logging.getLogger(__name__)


class SegmentService:
    """Service for segment operations."""

    def __init__(self):
        self.db = get_databricks_client()
        self.sql_gen = get_sql_generator()

    def preview_segment(
        self, segment: SegmentDefinition, include_sql: bool = True
    ) -> SegmentPreviewResponse:
        """Execute segment query and return preview counts."""
        # Generate SQL
        sql = self.sql_gen.generate_count_query(segment)
        logger.info(f"Preview SQL: {sql}")

        # Execute query
        start_time = time.time()
        result = self.db.execute_count_query(sql)
        execution_time_ms = (time.time() - start_time) * 1000

        return SegmentPreviewResponse(
            individual_count=result.get("individual_count", 0),
            household_count=result.get("household_count", 0),
            sql=sql if include_sql else None,
            execution_time_ms=execution_time_ms,
        )

    def build_segment(
        self,
        segment: SegmentDefinition,
        name: str,
        quarter: str,
        start_date: date,
        end_date: date,
    ) -> SegmentBuildResponse:
        """Build and save a segment to Databricks tables."""
        segment_id = str(uuid.uuid4())[:8]
        campaign_name = f"{name}_{segment_id}"

        # 1. Insert into segment_definitions
        definition_sql = f"""
INSERT INTO {get_definitions_table()}
(segment_name, segment_definition, quarter, start_date, end_date)
VALUES (
    '{campaign_name}',
    '{segment.description.replace("'", "''")}',
    '{quarter}',
    '{start_date.isoformat()}',
    '{end_date.isoformat()}'
)
        """.strip()

        logger.info(f"Inserting segment definition: {definition_sql}")
        self.db.execute_query(definition_sql)

        # 2. Insert into campaigns table (profile identity cols in SELECT, campaigns cols in INSERT)
        where_clause = self.sql_gen.generate_where_clause(segment)
        p_ind = get_profile_identity_individual_column()
        p_hh = get_profile_identity_household_column()
        c_ind = get_campaigns_identity_individual_column()
        c_hh = get_campaigns_identity_household_column()
        seg_col = get_campaigns_segment_name_column()
        campaigns_sql = f"""
INSERT INTO {get_campaigns_table()}
({c_ind}, {c_hh}, {seg_col})
SELECT {p_ind}, {p_hh}, '{campaign_name}'
FROM {get_profiles_table()}
WHERE {where_clause}
        """.strip()

        logger.info(f"Inserting campaign members: {campaigns_sql[:200]}...")
        self.db.execute_query(campaigns_sql)

        # 3. Count inserted rows
        seg_col = get_campaigns_segment_name_column()
        count_sql = f"""
SELECT COUNT(*) as count
FROM {get_campaigns_table()}
WHERE {seg_col} = '{campaign_name}'
        """.strip()

        result = self.db.execute_count_query(count_sql)
        rows_inserted = result.get("count", 0)

        return SegmentBuildResponse(
            segment_id=segment_id,
            rows_inserted=rows_inserted,
            campaign_name=campaign_name,
        )

    def list_segments(self) -> list[dict]:
        """List all existing segments."""
        sql = f"""
SELECT
    segment_name,
    segment_definition,
    quarter,
    start_date,
    end_date
FROM {get_definitions_table()}
ORDER BY segment_name
        """.strip()

        return self.db.execute_query(sql)

    def all_segments_overview(self) -> list[dict]:
        """Definitions joined with campaigns, grouped by campaign with individual/household counts."""
        c_ind = get_campaigns_identity_individual_column()
        c_hh = get_campaigns_identity_household_column()
        seg_col = get_campaigns_segment_name_column()
        sql = f"""
SELECT
    d.segment_name,
    d.segment_definition,
    d.quarter,
    d.start_date,
    d.end_date,
    COUNT(DISTINCT c.{c_ind}) AS individual_count,
    COUNT(DISTINCT c.{c_hh}) AS household_count
FROM {get_definitions_table()} d
LEFT JOIN {get_campaigns_table()} c ON d.segment_name = c.{seg_col}
GROUP BY d.segment_name, d.segment_definition, d.quarter, d.start_date, d.end_date
ORDER BY d.segment_name
        """.strip()

        return self.db.execute_query(sql)

    def update_segment_metadata(
        self,
        segment_name: str,
        segment_definition: str,
        quarter: str,
        start_date: date,
        end_date: date,
    ) -> None:
        """Update a segment's metadata in megacorp_segment_definitions."""
        # Escape single quotes for SQL
        safe_def = segment_definition.replace("'", "''")
        safe_name = segment_name.replace("'", "''")

        sql = f"""
UPDATE {get_definitions_table()}
SET
    segment_definition = '{safe_def}',
    quarter = '{quarter}',
    start_date = '{start_date.isoformat()}',
    end_date = '{end_date.isoformat()}'
WHERE segment_name = '{safe_name}'
        """.strip()

        logger.info("Updating segment metadata: %s", segment_name)
        self.db.execute_query(sql)


# Singleton instance
_service: SegmentService | None = None


def get_segment_service() -> SegmentService:
    """Get the singleton segment service."""
    global _service
    if _service is None:
        _service = SegmentService()
    return _service
