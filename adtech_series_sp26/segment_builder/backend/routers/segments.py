"""API routes for segment operations."""

import logging

from databricks.sql.exc import RequestError
from fastapi import APIRouter, Depends, HTTPException

from backend.models.segment import (
    SegmentBuildRequest,
    SegmentBuildResponse,
    SegmentPreviewRequest,
    SegmentPreviewResponse,
    SegmentUpdateRequest,
)
from backend.config.constants import GENERIC_ERROR_MESSAGE, get_databricks_forbidden_message
from backend.config.table_overrides import get_catalog_schemas_for_grants
from backend.services.databricks_client import DatabricksClient, get_databricks_client
from backend.services.segment_service import SegmentService, get_segment_service
from backend.services.sql_generator import SqlGenerator, SqlGeneratorError, get_sql_generator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/segment", tags=["segments"])


def _is_forbidden(err: RequestError) -> bool:
    """True if the Databricks error is 403 Forbidden (auth/perms)."""
    msg = (getattr(err, "message", None) or str(err)).upper()
    return "403" in msg or "FORBIDDEN" in msg


def _forbidden_detail() -> str:
    """403 detail message using current catalog/schema from settings."""
    ctx = get_catalog_schemas_for_grants()
    return get_databricks_forbidden_message(
        catalog=ctx.get("catalog"),
        profiles_schema=ctx.get("profiles_schema"),
        segments_schema=ctx.get("segments_schema"),
    )


@router.post("/preview", response_model=SegmentPreviewResponse)
async def preview_segment(
    request: SegmentPreviewRequest,
    db: DatabricksClient = Depends(get_databricks_client),
    service: SegmentService = Depends(get_segment_service),
    sql_gen: SqlGenerator = Depends(get_sql_generator),
):
    """Preview a segment - returns counts and generated SQL."""
    try:
        if not db.is_configured:
            # Return mock data if Databricks not configured
            sql = sql_gen.generate_count_query(request.segment)
            return SegmentPreviewResponse(
                individual_count=0,
                household_count=0,
                sql=sql if request.include_sql else None,
                execution_time_ms=0,
            )

        return service.preview_segment(request.segment, request.include_sql)

    except SqlGeneratorError as e:
        logger.error(
            "SQL generation error",
            extra={"error": str(e), "endpoint": "preview"},
        )
        raise HTTPException(status_code=400, detail=str(e))
    except RequestError as e:
        if _is_forbidden(e):
            logger.warning(
                "Databricks 403 on preview_segment",
                extra={"error": str(e), "endpoint": "preview"},
            )
            raise HTTPException(status_code=403, detail=_forbidden_detail())
        logger.exception(
            "Preview error",
            extra={"error": str(e), "endpoint": "preview"},
        )
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_MESSAGE)
    except Exception as e:
        logger.exception(
            "Preview error",
            extra={"error": str(e), "endpoint": "preview"},
        )
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_MESSAGE)


@router.post("/build", response_model=SegmentBuildResponse)
async def build_segment(
    request: SegmentBuildRequest,
    db: DatabricksClient = Depends(get_databricks_client),
    service: SegmentService = Depends(get_segment_service),
):
    """Build and save a segment to Databricks tables."""
    try:
        if not db.is_configured:
            raise HTTPException(
                status_code=503,
                detail="Databricks not configured. Cannot build segment."
            )

        return service.build_segment(
            segment=request.segment,
            name=request.name,
            quarter=request.quarter,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    except SqlGeneratorError as e:
        logger.error(
            "SQL generation error",
            extra={"error": str(e), "endpoint": "build"},
        )
        raise HTTPException(status_code=400, detail=str(e))
    except RequestError as e:
        if _is_forbidden(e):
            logger.warning(
                "Databricks 403 on build_segment",
                extra={"error": str(e), "endpoint": "build"},
            )
            raise HTTPException(status_code=403, detail=_forbidden_detail())
        logger.exception(
            "Build error",
            extra={"error": str(e), "endpoint": "build"},
        )
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_MESSAGE)
    except Exception as e:
        logger.exception(
            "Build error",
            extra={"error": str(e), "endpoint": "build"},
        )
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_MESSAGE)


@router.get("")
async def list_segments(
    db: DatabricksClient = Depends(get_databricks_client),
    service: SegmentService = Depends(get_segment_service),
):
    """List all existing segments."""
    try:
        if not db.is_configured:
            return {"segments": []}

        segments = service.list_segments()
        return {"segments": segments}

    except RequestError as e:
        if _is_forbidden(e):
            logger.warning(
                "Databricks 403 on list_segments",
                extra={"error": str(e), "endpoint": "list_segments"},
            )
            raise HTTPException(status_code=403, detail=_forbidden_detail())
        logger.exception(
            "List segments error",
            extra={"error": str(e), "endpoint": "list_segments"},
        )
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_MESSAGE)
    except Exception as e:
        logger.exception(
            "List segments error",
            extra={"error": str(e), "endpoint": "list_segments"},
        )
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_MESSAGE)


@router.get("/all")
async def all_segments_overview(
    db: DatabricksClient = Depends(get_databricks_client),
    service: SegmentService = Depends(get_segment_service),
):
    """All segments: definitions joined with campaigns, grouped by campaign with individual/household counts."""
    try:
        if not db.is_configured:
            return {"rows": []}

        rows = service.all_segments_overview()
        return {"rows": rows}

    except RequestError as e:
        if _is_forbidden(e):
            logger.warning(
                "Databricks 403 on all_segments_overview",
                extra={"error": str(e), "endpoint": "all_segments_overview"},
            )
            raise HTTPException(status_code=403, detail=_forbidden_detail())
        logger.exception(
            "All segments overview error",
            extra={"error": str(e), "endpoint": "all_segments_overview"},
        )
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_MESSAGE)
    except Exception as e:
        logger.exception(
            "All segments overview error",
            extra={"error": str(e), "endpoint": "all_segments_overview"},
        )
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_MESSAGE)


@router.patch("/{segment_name}")
async def update_segment_metadata(
    segment_name: str,
    request: SegmentUpdateRequest,
    db: DatabricksClient = Depends(get_databricks_client),
    service: SegmentService = Depends(get_segment_service),
):
    """Update segment metadata (definition, quarter, flight dates) in Delta table."""
    try:
        if not db.is_configured:
            raise HTTPException(
                status_code=503,
                detail="Databricks not configured. Cannot update segment.",
            )

        service.update_segment_metadata(
            segment_name=segment_name,
            segment_definition=request.segment_definition,
            quarter=request.quarter,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        return {"status": "updated", "segment_name": segment_name}

    except Exception as e:
        logger.exception(
            "Update segment error",
            extra={"error": str(e), "endpoint": "update_segment", "segment_name": segment_name},
        )
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_MESSAGE)
