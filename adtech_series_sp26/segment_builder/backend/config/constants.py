"""Shared constants for API responses."""

# Generic message returned for 500 errors (avoid leaking internal details to clients)
GENERIC_ERROR_MESSAGE = "An error occurred. Please try again."


def get_databricks_forbidden_message(
    catalog: str | None = None,
    profiles_schema: str | None = None,
    segments_schema: str | None = None,
) -> str:
    """Build 403 message using current table settings. Uses placeholder names if not set."""
    c = catalog or "catalog"
    p = profiles_schema or "profiles"
    s = segments_schema or "segments"
    return (
        f"Databricks access denied (403). In Databricks Apps the app runs as a service principal. "
        f"Grant that identity: USE_CATALOG on {c}; USE_SCHEMA and SELECT on {c}.{p}; "
        f"USE_SCHEMA, SELECT, and MODIFY on {c}.{s}. Get the app's client ID with: databricks apps get <app-name>"
    )
