from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(populate_by_name=True)

    PGHOST: str = ""
    PGDATABASE: str = "databricks_postgres"
    LAKEBASE_INSTANCE: str = "campaign-pacing"

    DATABRICKS_WAREHOUSE_ID: str = ""
    SEGMENT_DEFINITIONS_TABLE: str = (
        "media_advertising.segments.megacorp_segment_definitions"
    )


settings = Settings()
