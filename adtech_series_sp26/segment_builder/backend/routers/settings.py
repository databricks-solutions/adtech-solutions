"""API routes for app settings (e.g. table configuration)."""

import os
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.config.column_overrides import get_column_configs, set_column_config
from backend.config.table_overrides import get_catalog_schemas_for_grants, get_tables, set_table_overrides

router = APIRouter(prefix="/api/settings", tags=["settings"])

PRINCIPAL_PLACEHOLDER = "<service_principal_client_id>"


def _get_app_principal() -> str | None:
    """Return this app's identity when running in Databricks Apps (DATABRICKS_CLIENT_ID)."""
    client_id = (os.environ.get("DATABRICKS_CLIENT_ID") or "").strip()
    return client_id if client_id else None


class TablesSettingsBody(BaseModel):
    """Table names and optional column configs."""

    profiles_table: str = ""
    campaigns_table: str = ""
    definitions_table: str = ""
    column_configs: dict[str, Any] | None = None


@router.get("/grants-sql")
async def get_grants_sql():
    """Return Unity Catalog grant SQL for the current table settings (copy-paste ready).
    When running in Databricks Apps, the app's identity (DATABRICKS_CLIENT_ID) is detected
    and used in the SQL so no placeholder replacement is needed.
    """
    ctx = get_catalog_schemas_for_grants()
    catalog = ctx.get("catalog")
    profiles_schema = ctx.get("profiles_schema")
    segments_schema = ctx.get("segments_schema")

    principal = _get_app_principal()

    if not catalog:
        return {
            "sql": "-- Set table names above (catalog.schema.table) and save to generate grant SQL.",
            "principal_placeholder": PRINCIPAL_PLACEHOLDER,
            "principal_detected": principal,
        }

    if principal:
        lines = [
            "-- Unity Catalog grants for this app's tables.",
            f"-- Identity detected from this app (DATABRICKS_CLIENT_ID): {principal}",
            "",
            f"GRANT USE_CATALOG ON CATALOG {catalog} TO `{principal}`;",
            "",
        ]
    else:
        lines = [
            "-- Unity Catalog grants for this app's tables.",
            "-- Replace " + PRINCIPAL_PLACEHOLDER + " with your app's service principal client ID.",
            "-- In Databricks Apps this is set automatically (DATABRICKS_CLIENT_ID).",
            "-- Locally: databricks apps get <app-name> | grep service_principal_client_id",
            "",
            f"GRANT USE_CATALOG ON CATALOG {catalog} TO {PRINCIPAL_PLACEHOLDER};",
            "",
        ]

    to_sql = f"`{principal}`" if principal else PRINCIPAL_PLACEHOLDER
    if profiles_schema:
        lines.append("-- Profiles (read-only)")
        lines.append(
            f"GRANT USE_SCHEMA, SELECT ON SCHEMA {catalog}.{profiles_schema} TO {to_sql};"
        )
        lines.append("")
    if segments_schema:
        lines.append("-- Segments (read/write)")
        lines.append(
            f"GRANT USE_SCHEMA, SELECT, MODIFY ON SCHEMA {catalog}.{segments_schema} TO {to_sql};"
        )

    return {
        "sql": "\n".join(lines),
        "principal_placeholder": PRINCIPAL_PLACEHOLDER,
        "principal_detected": principal,
    }


@router.get("/tables")
async def get_settings_tables():
    """Return current table names and column configs."""
    data: dict[str, Any] = dict(get_tables())
    data["column_configs"] = get_column_configs()
    return data


@router.put("/tables")
async def put_settings_tables(body: TablesSettingsBody):
    """Update table name overrides and/or column configs."""
    set_table_overrides(
        profiles_table=body.profiles_table,
        campaigns_table=body.campaigns_table,
        definitions_table=body.definitions_table,
    )
    if body.column_configs:
        set_column_config(
            profile=body.column_configs.get("profile"),
            segment_list=body.column_configs.get("segment_list"),
            segment_info_labels=body.column_configs.get("segment_info_labels"),
        )
    data: dict[str, Any] = dict(get_tables())
    data["column_configs"] = get_column_configs()
    return data
