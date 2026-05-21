"""Databricks SQL connector wrapper."""

import logging
import os
from typing import Any

from databricks.sql.exc import RequestError

from backend.config.settings import get_settings
from backend.config.table_overrides import get_profiles_table

logger = logging.getLogger(__name__)


def _is_auth_403(err: RequestError) -> bool:
    """True if the error is a 403 FORBIDDEN auth/credential issue (e.g. expired token)."""
    msg = (getattr(err, "message", None) or str(err)).upper()
    return "403" in msg or "FORBIDDEN" in msg


class DatabricksClient:
    """Client for executing SQL queries against Databricks."""

    def __init__(self):
        self.settings = get_settings()
        self._connection = None
        self._use_sdk_auth = self._detect_databricks_apps_env()

    def _detect_databricks_apps_env(self) -> bool:
        """Detect if running in Databricks Apps environment (use SDK default auth)."""
        # Official Databricks Apps env vars: https://docs.databricks.com/dev-tools/databricks-apps/system-env
        return bool(
            os.environ.get("DATABRICKS_APP_NAME")
            or os.environ.get("DATABRICKS_HOST")
        )

    @property
    def is_configured(self) -> bool:
        """Check if Databricks is properly configured."""
        if self._use_sdk_auth:
            return True
        if self.settings.is_databricks_configured:
            return True
        return bool(self.settings.databricks_config_profile)

    def _get_workspace_client(self):
        """Create a WorkspaceClient (Apps default auth or profile for local dev). Prefer env vars over profile."""
        from databricks.sdk import WorkspaceClient
        if self._use_sdk_auth:
            return WorkspaceClient()
        if self.settings.is_databricks_configured:
            return None  # use env var path in _get_connection
        if self.settings.databricks_config_profile:
            return WorkspaceClient(profile=self.settings.databricks_config_profile)
        return None

    def _get_connection(self):
        """Get or create a Databricks SQL connection."""
        if self._connection is None:
            from databricks import sql

            w = self._get_workspace_client()
            if w is not None:
                # Apps or profile-based auth: use SDK to get host, warehouse, token
                auth_label = "Databricks Apps" if self._use_sdk_auth else f"profile '{self.settings.databricks_config_profile}'"
                logger.info("Using %s for SQL connection", auth_label)
                from databricks.sdk.service.sql import State

                host = w.config.host.replace("https://", "").replace("http://", "")
                warehouses = list(w.warehouses.list())
                running_warehouses = [wh for wh in warehouses if wh.state == State.RUNNING]
                if not running_warehouses:
                    raise RuntimeError("No running SQL warehouses available")
                warehouse = next(
                    (wh for wh in running_warehouses if "serverless" in wh.name.lower() or "shared" in wh.name.lower()),
                    running_warehouses[0],
                )
                logger.info("Using warehouse: %s (%s)", warehouse.name, warehouse.id)
                headers = w.config.authenticate()
                auth_header = headers.get("Authorization", "")
                if not auth_header.startswith("Bearer "):
                    raise RuntimeError("Failed to get OAuth token from Databricks SDK")
                token = auth_header.replace("Bearer ", "")
                self._connection = sql.connect(
                    server_hostname=host,
                    http_path=f"/sql/1.0/warehouses/{warehouse.id}",
                    access_token=token,
                )
            elif self.settings.is_databricks_configured:
                logger.info("Using environment variable authentication")
                self._connection = sql.connect(
                    server_hostname=self.settings.databricks_server_hostname,
                    http_path=self.settings.databricks_http_path,
                    access_token=self.settings.databricks_token,
                )
            else:
                raise RuntimeError(
                    "Databricks not configured. Set DATABRICKS_SERVER_HOSTNAME, "
                    "DATABRICKS_HTTP_PATH, and DATABRICKS_TOKEN, or set DATABRICKS_CONFIG_PROFILE for local dev."
                )
        return self._connection

    def execute_query(self, query: str) -> list[dict[str, Any]]:
        """Execute a SQL query and return results as list of dicts.
        On 403 (e.g. expired token), clears the cached connection and retries once.
        """
        last_error: RequestError | None = None
        for attempt in range(2):
            try:
                logger.info("Executing query: %s...", query[:200])
                connection = self._get_connection()
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
            except RequestError as e:
                last_error = e
                if attempt == 0 and _is_auth_403(e):
                    logger.warning(
                        "Databricks 403 (likely expired token), clearing connection and retrying once: %s",
                        e,
                    )
                    self._clear_connection()
                    continue
                raise
        if last_error:
            raise last_error
        return []

    def execute_count_query(self, query: str) -> dict[str, int]:
        """Execute a count query and return the first row as a dict."""
        results = self.execute_query(query)
        if results:
            return results[0]
        return {}

    def fetch_distinct_values(
        self,
        column: str,
        table: str | None = None,
        search: str | None = None,
        limit: int = 100,
    ) -> list[str]:
        """Fetch distinct values for a column."""
        if table is None:
            table = get_profiles_table()

        query = f"""
            SELECT DISTINCT {column}
            FROM {table}
            WHERE {column} IS NOT NULL
        """

        if search:
            query += f" AND LOWER({column}) LIKE LOWER('%{search}%')"

        query += f" ORDER BY {column} LIMIT {limit}"

        results = self.execute_query(query)
        return [str(row[column]) for row in results]

    def _clear_connection(self) -> None:
        """Close and clear the cached connection (e.g. after token expiry 403)."""
        if self._connection:
            try:
                self._connection.close()
            except Exception as e:
                logger.warning("Error closing Databricks connection: %s", e)
            self._connection = None

    def close(self):
        """Close the connection."""
        self._clear_connection()


# Singleton instance
_client: DatabricksClient | None = None


def get_databricks_client() -> DatabricksClient:
    """Get the singleton Databricks client."""
    global _client
    if _client is None:
        _client = DatabricksClient()
    return _client
