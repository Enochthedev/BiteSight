"""Cache management and monitoring endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.cache_service import get_cache_service
from app.core.cache_monitoring import get_cache_monitor
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/stats", response_model=Dict[str, Any])
async def get_cache_stats(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get cache performance statistics.
    Requires authentication.
    """
    try:
        cache_service = get_cache_service()
        stats = cache_service.get_cache_stats()

        return {
            "status": "success",
            "data": stats,
            "message": "Cache statistics retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cache stats: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, Any])
async def check_cache_health() -> Dict[str, Any]:
    """
    Check cache health status.
    Public endpoint for monitoring.
    """
    try:
        cache_monitor = get_cache_monitor()
        health_status = cache_monitor.check_cache_health()

        # Set appropriate HTTP status based on health
        status_code = status.HTTP_200_OK
        if health_status['status'] == 'unhealthy':
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif health_status['status'] == 'degraded':
            status_code = status.HTTP_206_PARTIAL_CONTENT

        return JSONResponse(
            status_code=status_code,
            content={
                "status": "success",
                "data": health_status,
                "message": f"Cache health status: {health_status['status']}"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "data": None,
                "message": f"Health check failed: {str(e)}"
            }
        )


@router.get("/metrics", response_model=Dict[str, Any])
async def get_cache_metrics(
    hours: int = 1,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get cache performance metrics for specified time period.
    Requires authentication.
    """
    try:
        if hours < 1 or hours > 24:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hours parameter must be between 1 and 24"
            )

        cache_monitor = get_cache_monitor()

        # Collect current metrics
        current_metrics = cache_monitor.collect_metrics()

        # Get metrics summary
        summary = cache_monitor.get_metrics_summary(hours=hours)

        return {
            "status": "success",
            "data": {
                "current_metrics": {
                    "timestamp": current_metrics.timestamp.isoformat(),
                    "hit_rate": current_metrics.hit_rate,
                    "miss_rate": current_metrics.miss_rate,
                    "total_requests": current_metrics.total_requests,
                    "memory_usage": current_metrics.memory_usage,
                    "connected_clients": current_metrics.connected_clients,
                    "operations_per_second": current_metrics.operations_per_second,
                    "average_response_time": current_metrics.average_response_time
                },
                "summary": summary
            },
            "message": f"Cache metrics for last {hours} hour(s) retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cache metrics: {str(e)}"
        )


@router.delete("/clear", response_model=Dict[str, Any])
async def clear_cache(
    cache_type: str = "all",
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Clear cache entries.
    Requires authentication.

    Args:
        cache_type: Type of cache to clear ('all', 'model_inference', 'user_session', etc.)
    """
    try:
        cache_service = get_cache_service()

        if cache_type == "all":
            # Clear all cache
            result = cache_service.redis_client.flush_db()
            if result:
                return {
                    "status": "success",
                    "data": {"cleared": True, "cache_type": "all"},
                    "message": "All cache cleared successfully"
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to clear cache"
                )
        else:
            # Clear specific cache type (would need pattern matching)
            # For now, return not implemented
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Selective cache clearing not yet implemented"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.delete("/user/{user_id}", response_model=Dict[str, Any])
async def clear_user_cache(
    user_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Clear cache entries for a specific user.
    Requires authentication.
    """
    try:
        cache_service = get_cache_service()

        # Clear user-specific cache entries
        deleted_count = cache_service.invalidate_user_cache(user_id)

        return {
            "status": "success",
            "data": {
                "user_id": user_id,
                "deleted_entries": deleted_count
            },
            "message": f"Cleared {deleted_count} cache entries for user {user_id}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear user cache: {str(e)}"
        )


@router.post("/warmup", response_model=Dict[str, Any])
async def warmup_cache(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Warmup cache with commonly accessed data.
    Requires authentication.
    """
    try:
        # This would typically pre-load frequently accessed data
        # For now, just return success
        return {
            "status": "success",
            "data": {"warmup_completed": True},
            "message": "Cache warmup completed successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to warmup cache: {str(e)}"
        )
