"""Pydantic models for segment definitions and API requests/responses."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class SegmentCondition(BaseModel):
    """A single condition in a segment rule."""

    id: str = Field(..., description="Unique identifier for this condition")
    feature: str = Field(..., description="Column name (e.g., 'age', 'state')")
    operator: Literal["IS", "IN", "NOT", "BETWEEN", "GT", "LT", "GTE", "LTE"] = Field(
        ..., description="Comparison operator"
    )
    values: list[str | int | float | bool] = Field(
        ..., description="Values to compare against"
    )


class SegmentGroup(BaseModel):
    """A group of conditions combined with AND/OR logic."""

    id: str = Field(..., description="Unique identifier for this group")
    logic: Literal["AND", "OR"] = Field(
        default="AND", description="Logic operator between conditions"
    )
    conditions: list[SegmentCondition] = Field(
        default_factory=list, description="List of conditions in this group"
    )


class SegmentDefinition(BaseModel):
    """Complete segment definition with groups of conditions."""

    name: str = Field(default="", description="Segment name")
    description: str = Field(default="", description="Human-readable description")
    groups: list[SegmentGroup] = Field(
        default_factory=list, description="Groups of conditions"
    )
    group_logic: Literal["AND", "OR"] = Field(
        default="AND", description="Logic operator between groups"
    )


# API Request/Response Models


class SegmentPreviewRequest(BaseModel):
    """Request to preview a segment."""

    segment: SegmentDefinition
    include_sql: bool = Field(default=True, description="Include generated SQL in response")


class SegmentPreviewResponse(BaseModel):
    """Response from segment preview."""

    individual_count: int = Field(..., description="Count of unique individuals")
    household_count: int = Field(..., description="Count of unique households")
    sql: str | None = Field(None, description="Generated SQL query")
    execution_time_ms: float = Field(..., description="Query execution time in milliseconds")


class SegmentBuildRequest(BaseModel):
    """Request to build and save a segment."""

    segment: SegmentDefinition
    name: str = Field(..., description="Segment name for saving")
    quarter: str = Field(..., description="Fiscal quarter (e.g., 'Q1')")
    start_date: date = Field(..., description="Campaign start date")
    end_date: date = Field(..., description="Campaign end date")


class SegmentBuildResponse(BaseModel):
    """Response from building a segment."""

    segment_id: str = Field(..., description="Generated segment ID")
    rows_inserted: int = Field(..., description="Number of rows inserted into campaigns")
    campaign_name: str = Field(..., description="Campaign name in the database")


class SegmentUpdateRequest(BaseModel):
    """Request to update segment metadata (definition, quarter, flight dates)."""

    segment_definition: str = Field(..., description="Human-readable segment description")
    quarter: str = Field(..., description="Fiscal quarter (e.g., '25Q1')")
    start_date: date = Field(..., description="Flight start date")
    end_date: date = Field(..., description="Flight end date")


class FeatureResponse(BaseModel):
    """Response for a single feature."""

    name: str
    display_name: str
    column: str
    type: str
    operators: list[str]
    description: str
    nullable: bool = False
    null_rate: float | None = None
    distinct_values: int | None = None
    values: list[str] | None = None
    searchable: bool = False
    range: dict[str, int] | None = None
    brackets: list[dict] | None = None


class FeaturesListResponse(BaseModel):
    """Response for listing all features."""

    features: list[FeatureResponse]


class FeatureValuesResponse(BaseModel):
    """Response for feature values."""

    values: list[str]
    total: int
