"""Pytest fixtures and configuration."""

import pytest

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(autouse=True)
def patch_table_and_column_config(monkeypatch):
    """Patch table and column overrides so tests don't depend on env or overrides."""
    from backend.config import table_overrides
    from backend.config import column_overrides

    monkeypatch.setattr(
        table_overrides,
        "get_profiles_table",
        lambda: "media_advertising.profiles.megacorp_audience_census_profile",
    )
    monkeypatch.setattr(
        column_overrides,
        "get_profile_identity_individual_column",
        lambda: "megacorp_indid",
    )
    monkeypatch.setattr(
        column_overrides,
        "get_profile_identity_household_column",
        lambda: "megacorp_hhid",
    )
