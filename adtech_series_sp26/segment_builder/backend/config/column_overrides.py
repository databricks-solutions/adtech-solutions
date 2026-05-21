"""In-memory overrides for column names and UI labels. Used by Settings API."""

import re
from typing import Any

# Defaults matching current schema
DEFAULT_PROFILE = {
    "features_layout": "by_column",
    "identity_household_column": "megacorp_hhid",
    "identity_individual_column": "megacorp_indid",
}
DEFAULT_SEGMENT_LIST = {
    "identity_household_column": "megacorp_hhid",
    "identity_individual_column": "megacorp_indid",
    "segment_name_column": "campaign_name",
}
DEFAULT_SEGMENT_INFO_LABELS: dict[str, str] = {
    "segment_name": "Segment Name",
    "segment_definition": "Segment Definition",
    "quarter": "Quarter",
    "start_date": "Flight Start Date",
    "end_date": "Flight End Date",
    "megacorp_indid": "Individual Identifier",
    "megacorp_hhid": "Household Identifier",
}

_overrides: dict[str, Any] = {}


def _safe_column(name: str) -> str:
    """Allow only alphanumeric and underscore for column names."""
    if not name or not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        return ""
    return name


def set_column_config(
    *,
    profile: dict[str, Any] | None = None,
    segment_list: dict[str, Any] | None = None,
    segment_info_labels: dict[str, str] | None = None,
) -> None:
    """Replace or merge column config. Pass full dict per section to replace."""
    if "column_configs" not in _overrides:
        _overrides["column_configs"] = {
            "profile": dict(DEFAULT_PROFILE),
            "segment_list": dict(DEFAULT_SEGMENT_LIST),
            "segment_info_labels": dict(DEFAULT_SEGMENT_INFO_LABELS),
        }
    cfg = _overrides["column_configs"]
    if profile is not None:
        cfg["profile"] = {**DEFAULT_PROFILE, **profile}
        cfg["profile"]["identity_household_column"] = _safe_column(
            cfg["profile"].get("identity_household_column", "")
        ) or DEFAULT_PROFILE["identity_household_column"]
        cfg["profile"]["identity_individual_column"] = _safe_column(
            cfg["profile"].get("identity_individual_column", "")
        ) or DEFAULT_PROFILE["identity_individual_column"]
        if cfg["profile"].get("features_layout") not in ("by_column", "by_row"):
            cfg["profile"]["features_layout"] = DEFAULT_PROFILE["features_layout"]
    if segment_list is not None:
        cfg["segment_list"] = {**DEFAULT_SEGMENT_LIST, **segment_list}
        cfg["segment_list"]["identity_household_column"] = _safe_column(
            cfg["segment_list"].get("identity_household_column", "")
        ) or DEFAULT_SEGMENT_LIST["identity_household_column"]
        cfg["segment_list"]["identity_individual_column"] = _safe_column(
            cfg["segment_list"].get("identity_individual_column", "")
        ) or DEFAULT_SEGMENT_LIST["identity_individual_column"]
        cfg["segment_list"]["segment_name_column"] = _safe_column(
            cfg["segment_list"].get("segment_name_column", "")
        ) or DEFAULT_SEGMENT_LIST["segment_name_column"]
    if segment_info_labels is not None:
        cfg["segment_info_labels"] = {**DEFAULT_SEGMENT_INFO_LABELS, **segment_info_labels}


def get_column_configs() -> dict[str, Any]:
    """Return full column config (for API)."""
    if "column_configs" not in _overrides:
        _overrides["column_configs"] = {
            "profile": dict(DEFAULT_PROFILE),
            "segment_list": dict(DEFAULT_SEGMENT_LIST),
            "segment_info_labels": dict(DEFAULT_SEGMENT_INFO_LABELS),
        }
    return _overrides["column_configs"]


def get_profile_identity_household_column() -> str:
    return get_column_configs()["profile"].get(
        "identity_household_column", DEFAULT_PROFILE["identity_household_column"]
    )


def get_profile_identity_individual_column() -> str:
    return get_column_configs()["profile"].get(
        "identity_individual_column", DEFAULT_PROFILE["identity_individual_column"]
    )


def get_campaigns_identity_household_column() -> str:
    return get_column_configs()["segment_list"].get(
        "identity_household_column", DEFAULT_SEGMENT_LIST["identity_household_column"]
    )


def get_campaigns_identity_individual_column() -> str:
    return get_column_configs()["segment_list"].get(
        "identity_individual_column", DEFAULT_SEGMENT_LIST["identity_individual_column"]
    )


def get_campaigns_segment_name_column() -> str:
    return get_column_configs()["segment_list"].get(
        "segment_name_column", DEFAULT_SEGMENT_LIST["segment_name_column"]
    )


def get_segment_info_column_labels() -> dict[str, str]:
    return dict(
        get_column_configs().get("segment_info_labels", DEFAULT_SEGMENT_INFO_LABELS)
    )
