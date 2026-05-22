"""In-memory overrides for Unity Catalog table names. Used by Settings API."""

from backend.config.settings import get_settings

_overrides: dict[str, str] = {}


def set_table_overrides(
    *,
    profiles_table: str | None = None,
    campaigns_table: str | None = None,
    definitions_table: str | None = None,
) -> None:
    """Set table name overrides. None = leave unchanged; empty string = clear (use default)."""
    if profiles_table is not None:
        if profiles_table == "":
            _overrides.pop("profiles_table", None)
        else:
            _overrides["profiles_table"] = profiles_table
    if campaigns_table is not None:
        if campaigns_table == "":
            _overrides.pop("campaigns_table", None)
        else:
            _overrides["campaigns_table"] = campaigns_table
    if definitions_table is not None:
        if definitions_table == "":
            _overrides.pop("definitions_table", None)
        else:
            _overrides["definitions_table"] = definitions_table


def get_profiles_table() -> str:
    """Profiles (audience census) table. Override or config default."""
    return _overrides.get("profiles_table") or get_settings().profiles_table


def get_campaigns_table() -> str:
    """Campaigns / segment list table. Override or config default."""
    return _overrides.get("campaigns_table") or get_settings().campaigns_table


def get_definitions_table() -> str:
    """Segment definitions table. Override or config default."""
    return _overrides.get("definitions_table") or get_settings().definitions_table


def get_tables() -> dict[str, str]:
    """Return current table names (overrides or defaults)."""
    return {
        "profiles_table": get_profiles_table(),
        "campaigns_table": get_campaigns_table(),
        "definitions_table": get_definitions_table(),
    }


def _parse_catalog_schema(fully_qualified: str) -> tuple[str, str] | None:
    """Return (catalog, schema) from 'catalog.schema.table' or None if invalid."""
    parts = (fully_qualified or "").strip().split(".")
    if len(parts) >= 3:
        return (parts[0], parts[1])
    return None


def get_catalog_schemas_for_grants() -> dict[str, str | None]:
    """Return catalog and schema names from current table settings (for error messages and grants).
    Keys: catalog, profiles_schema, segments_schema. Values are None when not determinable.
    """
    tables = get_tables()
    profiles = _parse_catalog_schema(tables.get("profiles_table", ""))
    campaigns = _parse_catalog_schema(tables.get("campaigns_table", ""))
    definitions = _parse_catalog_schema(tables.get("definitions_table", ""))

    catalog: str | None = None
    profiles_schema: str | None = None
    segments_schema: str | None = None

    if profiles:
        catalog, profiles_schema = profiles
    if campaigns:
        c, segments_schema = campaigns
        if catalog is None:
            catalog = c
    if definitions and segments_schema is None:
        c, segments_schema = definitions
        if catalog is None:
            catalog = c

    return {
        "catalog": catalog,
        "profiles_schema": profiles_schema,
        "segments_schema": segments_schema,
    }
