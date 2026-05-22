"""
Fetches campaign segment definitions from the Delta table via SQL warehouse.

The result is cached in-process for SEGMENT_DEFINITIONS_CACHE_SECONDS to avoid
hitting the warehouse on every dashboard refresh (2s poll cadence).
"""
import logging
import time
from typing import Dict

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

from .config import settings

logger = logging.getLogger(__name__)

_CACHE: Dict[str, str] = {}
_CACHE_LOADED_AT: float = 0.0
_CACHE_TTL_SECONDS = 300

_client = WorkspaceClient()


def _fetch_definitions() -> Dict[str, str]:
    if not settings.DATABRICKS_WAREHOUSE_ID:
        logger.info("DATABRICKS_WAREHOUSE_ID not set; segment definitions disabled.")
        return {}

    sql = (
        f"SELECT segment_name, segment_definition "
        f"FROM {settings.SEGMENT_DEFINITIONS_TABLE} "
        f"WHERE segment_definition IS NOT NULL"
    )

    resp = _client.statement_execution.execute_statement(
        warehouse_id=settings.DATABRICKS_WAREHOUSE_ID,
        statement=sql,
        wait_timeout="30s",
    )

    if resp.status and resp.status.state != StatementState.SUCCEEDED:
        logger.warning("Definitions query failed: %s", resp.status)
        return {}

    out: Dict[str, str] = {}
    if resp.result and resp.result.data_array:
        for row in resp.result.data_array:
            if row and len(row) >= 2 and row[0] and row[1]:
                out[row[0]] = row[1]
    return out


def get_definitions() -> Dict[str, str]:
    """Return {segment_name: segment_definition}, cached for 5 minutes."""
    global _CACHE, _CACHE_LOADED_AT
    now = time.time()
    if not _CACHE or (now - _CACHE_LOADED_AT) > _CACHE_TTL_SECONDS:
        try:
            _CACHE = _fetch_definitions()
            _CACHE_LOADED_AT = now
            logger.info("Loaded %d segment definitions.", len(_CACHE))
        except Exception:
            logger.exception("Failed to load segment definitions; keeping stale cache.")
    return _CACHE
