"""Feature metadata for the 14 audience profile columns."""

from typing import Any

# Feature type definitions
FEATURE_TYPES = {
    "categorical": "categorical",
    "numeric": "numeric",
    "boolean": "boolean"
}

# All available features with their metadata
FEATURES: dict[str, dict[str, Any]] = {
    "state": {
        "display_name": "State",
        "column": "state",
        "type": "categorical",
        "operators": ["IS", "IN", "NOT"],
        "description": "US state or territory code (2-letter)",
        "nullable": False,
        "distinct_values": 57,
    },
    "zip5": {
        "display_name": "ZIP Code",
        "column": "zip5",
        "type": "categorical",
        "operators": ["IS", "IN", "NOT"],
        "description": "5-digit ZIP code",
        "nullable": False,
        "distinct_values": 40328,
        "searchable": True,  # Too many values, use search
    },
    "age": {
        "display_name": "Age",
        "column": "age",
        "type": "numeric",
        "operators": ["IN", "NOT", "IS", "BETWEEN", "GT", "LT", "GTE", "LTE"],
        "description": "Age in years (18-115)",
        "nullable": True,
        "null_rate": 0.05,
        "range": {"min": 18, "max": 115},
        "bracket_style": "inclusive",
        "brackets": [
            {"label": "Under 18", "max": 17},
            {"label": "18-24", "min": 18, "max": 24},
            {"label": "25-34", "min": 25, "max": 34},
            {"label": "35-44", "min": 35, "max": 44},
            {"label": "45-54", "min": 45, "max": 54},
            {"label": "55-64", "min": 55, "max": 64},
            {"label": "65+", "min": 65},
        ],
    },
    "gender": {
        "display_name": "Gender",
        "column": "gender",
        "type": "categorical",
        "operators": ["IS", "IN", "NOT"],
        "description": "Gender classification",
        "nullable": False,
        "distinct_values": 5,
        "values": ["Male", "Female", "Unknown", "Other", "Prefer not to say"],
    },
    "is_dog_owner": {
        "display_name": "Dog Owner",
        "column": "is_dog_owner",
        "type": "boolean",
        "operators": ["IS"],
        "description": "Owns a dog",
        "nullable": True,
        "null_rate": 0.23,
    },
    "is_cat_owner": {
        "display_name": "Cat Owner",
        "column": "is_cat_owner",
        "type": "boolean",
        "operators": ["IS"],
        "description": "Owns a cat",
        "nullable": True,
        "null_rate": 0.57,
    },
    "qsr_propensity": {
        "display_name": "QSR Propensity",
        "column": "qsr_propensity",
        "type": "categorical",
        "operators": ["IS", "IN", "NOT"],
        "description": "Quick-service restaurant propensity score",
        "nullable": True,
        "null_rate": 0.31,
        "distinct_values": 4,
        "values": ["Low", "Medium", "High", "Very High"],
    },
    "martial_status": {
        "display_name": "Marital Status",
        "column": "martial_status",
        "type": "categorical",
        "operators": ["IS", "IN", "NOT"],
        "description": "Marital status",
        "nullable": False,
        "distinct_values": 5,
        "values": ["Single", "Married", "Divorced", "Widowed", "Unknown"],
    },
    "income_level": {
        "display_name": "Income Level",
        "column": "income_level",
        "type": "numeric",
        "operators": ["IN", "NOT", "IS", "BETWEEN", "GT", "LT", "GTE", "LTE"],
        "description": "Annual household income",
        "nullable": False,
        "bracket_style": "exclusive_upper",
        "brackets": [
            {"label": "<10K", "max": 10000},
            {"label": "10K-15K", "min": 10000, "max": 15000},
            {"label": "15K-25K", "min": 15000, "max": 25000},
            {"label": "25K-35K", "min": 25000, "max": 35000},
            {"label": "35K-50K", "min": 35000, "max": 50000},
            {"label": "50K-75K", "min": 50000, "max": 75000},
            {"label": "75K-100K", "min": 75000, "max": 100000},
            {"label": "100K-150K", "min": 100000, "max": 150000},
            {"label": "150K-200K", "min": 150000, "max": 200000},
            {"label": "200K+", "min": 200000},
        ],
    },
    "education_level": {
        "display_name": "Education Level",
        "column": "education_level",
        "type": "categorical",
        "operators": ["IS", "IN", "NOT"],
        "description": "Highest education attained",
        "nullable": False,
        "distinct_values": 4,
        "values": ["High School", "Some College", "Bachelor's", "Graduate"],
    },
    "is_active_auto_loan": {
        "display_name": "Active Auto Loan",
        "column": "is_active_auto_loan",
        "type": "boolean",
        "operators": ["IS"],
        "description": "Currently has auto loan",
        "nullable": True,
        "null_rate": 0.07,
    },
    "is_cord_cutter": {
        "display_name": "Cord Cutter",
        "column": "is_cord_cutter",
        "type": "boolean",
        "operators": ["IS"],
        "description": "No traditional cable subscription",
        "nullable": True,
        "null_rate": 0.46,
    },
    "luxury_propensity": {
        "display_name": "Luxury Propensity",
        "column": "luxury_propensity",
        "type": "categorical",
        "operators": ["IS", "IN", "NOT"],
        "description": "Luxury goods purchase propensity",
        "nullable": True,
        "null_rate": 0.31,
        "distinct_values": 6,
        "values": ["Very Low", "Low", "Medium", "High", "Very High", "Ultra"],
    },
    "auto_intenders": {
        "display_name": "Auto Intenders",
        "column": "auto_intenders",
        "type": "boolean",
        "operators": ["IS"],
        "description": "In-market for vehicle purchase",
        "nullable": True,
        "null_rate": 0.15,
    },
}

# Safe columns whitelist for SQL injection prevention
SAFE_COLUMNS = set(FEATURES.keys())


def get_feature(name: str) -> dict[str, Any] | None:
    """Get feature metadata by name."""
    return FEATURES.get(name)


def get_all_features() -> list[dict[str, Any]]:
    """Get all features as a list with names included."""
    return [
        {"name": name, **metadata}
        for name, metadata in FEATURES.items()
    ]
