"""API routes for feature metadata."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.config.constants import GENERIC_ERROR_MESSAGE
from backend.config.features import get_all_features, get_feature
from backend.models.segment import FeatureResponse, FeatureValuesResponse, FeaturesListResponse
from backend.services.databricks_client import DatabricksClient, get_databricks_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/features", tags=["features"])


@router.get("", response_model=FeaturesListResponse)
async def list_features():
    """List all available features with their metadata."""
    features_data = get_all_features()

    features = []
    for f in features_data:
        features.append(
            FeatureResponse(
                name=f["name"],
                display_name=f["display_name"],
                column=f["column"],
                type=f["type"],
                operators=f["operators"],
                description=f["description"],
                nullable=f.get("nullable", False),
                null_rate=f.get("null_rate"),
                distinct_values=f.get("distinct_values"),
                values=f.get("values"),
                searchable=f.get("searchable", False),
                range=f.get("range"),
                brackets=f.get("brackets"),
            )
        )

    return FeaturesListResponse(features=features)


@router.get("/{feature_name}/values", response_model=FeatureValuesResponse)
async def get_feature_values(
    feature_name: str,
    search: str | None = Query(None, description="Search filter"),
    limit: int = Query(100, le=1000, description="Maximum values to return"),
    db: DatabricksClient = Depends(get_databricks_client),
):
    """Get distinct values for a categorical feature."""
    feature = get_feature(feature_name)

    if not feature:
        raise HTTPException(status_code=404, detail=f"Feature not found: {feature_name}")

    if feature["type"] not in ("categorical",):
        raise HTTPException(
            status_code=400,
            detail=f"Feature {feature_name} is not categorical"
        )

    # If feature has static values and no search, return them
    if "values" in feature and not search:
        values = feature["values"][:limit]
        return FeatureValuesResponse(values=values, total=len(feature["values"]))

    # Otherwise, query Databricks
    try:
        values = db.fetch_distinct_values(
            column=feature["column"],
            search=search,
            limit=limit,
        )
        return FeatureValuesResponse(values=values, total=len(values))
    except Exception as e:
        # If Databricks not configured, return static values if available
        if "values" in feature:
            values = feature["values"]
            if search:
                values = [v for v in values if search.lower() in v.lower()]
            return FeatureValuesResponse(values=values[:limit], total=len(values))
        logger.exception(
            "Feature values error",
            extra={"error": str(e), "endpoint": "get_feature_values", "feature_name": feature_name},
        )
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_MESSAGE)
