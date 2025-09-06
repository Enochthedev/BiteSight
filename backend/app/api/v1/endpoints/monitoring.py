"""Monitoring and health check endpoints."""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Query, Depends
from fastapi.responses import JSONResponse

from app.core.health_checks import get_health_checker, HealthStatus
from app.core.async_tasks import get_task_processor
from app.core.orchestration import get_orchestrator
from app.core.dependencies import get_current_user
from app.models.user import Student

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.

    Returns detailed health information for all system components.
    """
    health_checker = get_health_checker()
    results = await health_checker.run_all_checks()
    overall_status = health_checker.get_overall_status(results)

    # Convert results to serializable format
    health_data = {}
    for name, result in results.items():
        health_data[name] = {
            "status": result.status.value,
            "message": result.message,
            "response_time": result.response_time,
            "timestamp": result.timestamp,
            "details": result.details
        }

    response_data = {
        "overall_status": overall_status.value,
        "service": "nutrition-feedback-api",
        "version": "1.0.0",
        "checks": health_data,
        "summary": {
            "total_checks": len(results),
            "healthy": sum(1 for r in results.values() if r.status == HealthStatus.HEALTHY),
            "degraded": sum(1 for r in results.values() if r.status == HealthStatus.DEGRADED),
            "unhealthy": sum(1 for r in results.values() if r.status == HealthStatus.UNHEALTHY)
        }
    }

    # Set appropriate HTTP status code
    if overall_status == HealthStatus.HEALTHY:
        status_code = 200
    elif overall_status == HealthStatus.DEGRADED:
        status_code = 200  # Still operational
    else:
        status_code = 503  # Service unavailable

    return JSONResponse(content=response_data, status_code=status_code)


@router.get("/health/{check_name}")
async def specific_health_check(check_name: str):
    """
    Run a specific health check.

    Args:
        check_name: Name of the health check to run
    """
    health_checker = get_health_checker()
    result = await health_checker.run_check(check_name)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Health check '{check_name}' not found"
        )

    response_data = {
        "check_name": check_name,
        "status": result.status.value,
        "message": result.message,
        "response_time": result.response_time,
        "timestamp": result.timestamp,
        "details": result.details
    }

    # Set appropriate HTTP status code
    if result.status == HealthStatus.HEALTHY:
        status_code = 200
    elif result.status == HealthStatus.DEGRADED:
        status_code = 200
    else:
        status_code = 503

    return JSONResponse(content=response_data, status_code=status_code)


@router.get("/metrics")
async def system_metrics():
    """
    Get system performance metrics.

    Returns metrics about task processing, queue status, and system performance.
    """
    try:
        # Get async task processor stats
        task_processor = await get_task_processor()
        task_stats = await task_processor.get_queue_stats()

        # Get orchestrator stats
        orchestrator = get_orchestrator()
        orchestrator_stats = {
            "running_tasks": len(orchestrator.running_tasks),
            "completed_tasks": len(orchestrator.task_results),
            "max_concurrent": orchestrator.max_concurrent_tasks
        }

        return {
            "service": "nutrition-feedback-api",
            "timestamp": __import__('time').time(),
            "async_tasks": task_stats,
            "orchestration": orchestrator_stats,
            "system": {
                "uptime": "calculated_at_runtime",  # Would need startup time tracking
                "version": "1.0.0"
            }
        }

    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system metrics"
        )


@router.get("/tasks/status")
async def task_queue_status():
    """
    Get async task queue status and statistics.
    """
    try:
        task_processor = await get_task_processor()
        stats = await task_processor.get_queue_stats()

        return {
            "queue_status": "operational" if stats["running"] else "stopped",
            "statistics": stats,
            "timestamp": __import__('time').time()
        }

    except Exception as e:
        logger.error(f"Failed to get task queue status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task queue status"
        )


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a specific async task.

    Args:
        task_id: ID of the task to check
    """
    try:
        task_processor = await get_task_processor()
        task_status = await task_processor.get_task_status(task_id)

        if task_status is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        return task_status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get task status for {task_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task status"
        )


@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: Student = Depends(get_current_user)
):
    """
    Cancel a running async task.

    Args:
        task_id: ID of the task to cancel
    """
    try:
        task_processor = await get_task_processor()
        cancelled = await task_processor.cancel_task(task_id)

        if not cancelled:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found or cannot be cancelled"
            )

        return {
            "message": f"Task {task_id} cancelled successfully",
            "task_id": task_id,
            "timestamp": __import__('time').time()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel task"
        )


@router.post("/maintenance/cleanup")
async def cleanup_old_data(
    max_age_hours: int = Query(
        24, description="Maximum age of data to keep in hours"),
    current_user: Student = Depends(get_current_user)
):
    """
    Clean up old completed tasks and temporary data.

    Args:
        max_age_hours: Maximum age of data to keep (in hours)
    """
    try:
        max_age_seconds = max_age_hours * 3600

        # Cleanup async tasks
        task_processor = await get_task_processor()
        await task_processor.cleanup_completed_tasks(max_age_seconds)

        # Cleanup orchestrator tasks
        orchestrator = get_orchestrator()
        orchestrator.cleanup_completed_tasks(max_age_seconds)

        return {
            "message": f"Cleanup completed for data older than {max_age_hours} hours",
            "max_age_hours": max_age_hours,
            "timestamp": __import__('time').time()
        }

    except Exception as e:
        logger.error(f"Failed to cleanup old data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup old data"
        )


@router.get("/ping")
async def ping():
    """
    Simple ping endpoint for basic availability checking.

    Returns a minimal response to verify the service is responding.
    """
    return {
        "status": "ok",
        "service": "nutrition-feedback-api",
        "timestamp": __import__('time').time()
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint for container orchestration.

    Checks if the service is ready to handle requests.
    """
    try:
        # Check critical dependencies
        health_checker = get_health_checker()

        # Run critical health checks
        critical_checks = ["database", "file_system"]
        results = {}

        for check_name in critical_checks:
            result = await health_checker.run_check(check_name)
            if result:
                results[check_name] = result.status

        # Service is ready if all critical checks pass
        all_healthy = all(
            status == HealthStatus.HEALTHY
            for status in results.values()
        )

        if all_healthy:
            return JSONResponse(
                content={
                    "status": "ready",
                    "service": "nutrition-feedback-api",
                    "checks": {name: status.value for name, status in results.items()},
                    "timestamp": __import__('time').time()
                },
                status_code=200
            )
        else:
            return JSONResponse(
                content={
                    "status": "not_ready",
                    "service": "nutrition-feedback-api",
                    "checks": {name: status.value for name, status in results.items()},
                    "timestamp": __import__('time').time()
                },
                status_code=503
            )

    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        return JSONResponse(
            content={
                "status": "not_ready",
                "error": str(e),
                "timestamp": __import__('time').time()
            },
            status_code=503
        )
