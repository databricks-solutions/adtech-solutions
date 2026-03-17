from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(populate_by_name=True)

    PGHOST: str = ""
    PGDATABASE: str = "databricks_postgres"
    LAKEBASE_INSTANCE: str = "campaign-pacing"


settings = Settings()
