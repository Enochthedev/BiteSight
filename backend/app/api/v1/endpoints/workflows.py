"""Workflow orchestration endpoints."""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from app.core.orchestration import get_orchestrator, MealAnalysisWorkflow
from app.core.async_tasks import get_task_processor, TaskPriority
from app.core.error_handling import workflow_error_response, get_error_handler
from app.core.dependencies import get_current_user
from app.models.user import Student

logger = logging.getLogger(__name__)

router = APIRouter()


class MealAnalysisRequest(BaseModel):
    """Request model for meal analysis workflow."""
    meal_id: str = Field(..., description="Unique meal identifier")
    image_path: str = Field(..., description="Path to the meal image")
    options: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional workflow options")


class BatchMealAnalysisRequest(BaseModel):
    """Request model for batch meal analysis."""
    meal_requests: List[Dict[str, str]
                        ] = Field(..., description="List of meal analysis requests")
    max_concurrent: Optional[int] = Field(
        default=5, description="Maximum concurrent analyses")


class WeeklyInsightsRequest(BaseModel):
    """Request model for weekly insights generation."""
    week_start: Optional[str] = Field(
        default=None, description="Week start date (YYYY-MM-DD)")


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    workflow_id: str
    status: str
    progress: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float
    updated_at: float


@router.post("/meals/analyze", response_model=WorkflowStatusResponse)
async def start_meal_analysis_workflow(
    request: MealAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: Student = Depends(get_current_user)
):
    """
    Start a meal analysis workflow.

    This endpoint initiates the complete meal analysis process including:
    - Image validation and preprocessing
    - Food recognition using ML models
    - Nutritional feedback generation
    - History storage (if enabled)
    """
    try:
        orchestrator = get_orchestrator()
        meal_workflow = MealAnalysisWorkflow(orchestrator)

        # Start the workflow asynchronously
        async def run_workflow():
            try:
                result = await meal_workflow.analyze_meal_complete(
                    student_id=str(current_user.student_id),
                    meal_id=request.meal_id,
                    image_path=request.image_path,
                    options=request.options
                )
                logger.info(
                    f"Meal analysis workflow completed for meal {request.meal_id}")
                return result
            except Exception as e:
                logger.error(
                    f"Meal analysis workflow failed for meal {request.meal_id}: {e}", exc_info=True)
                raise

        # Submit as async task
        task_processor = await get_task_processor()
        task_id = await task_processor.submit_task(
            f"meal_analysis_{request.meal_id}",
            run_workflow,
            priority=TaskPriority.HIGH
        )

        return WorkflowStatusResponse(
            workflow_id=task_id,
            status="started",
            created_at=__import__('time').time(),
            updated_at=__import__('time').time()
        )

    except Exception as e:
        logger.error(
            f"Failed to start meal analysis workflow: {e}", exc_info=True)
        return workflow_error_response(e, "meal_analysis")


@router.post("/meals/analyze/batch", response_model=WorkflowStatusResponse)
async def start_batch_meal_analysis_workflow(
    request: BatchMealAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: Student = Depends(get_current_user)
):
    """
    Start a batch meal analysis workflow for multiple meals.

    Processes multiple meal images in parallel with concurrency control.
    """
    try:
        orchestrator = get_orchestrator()
        meal_workflow = MealAnalysisWorkflow(orchestrator)

        # Validate that all requests belong to the current user
        for meal_request in request.meal_requests:
            if meal_request.get("student_id") != str(current_user.student_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot analyze meals for other users"
                )

        # Start the batch workflow asynchronously
        async def run_batch_workflow():
            try:
                results = await meal_workflow.batch_meal_analysis(request.meal_requests)
                logger.info(
                    f"Batch meal analysis completed for {len(request.meal_requests)} meals")
                return results
            except Exception as e:
                logger.error(
                    f"Batch meal analysis workflow failed: {e}", exc_info=True)
                raise

        # Submit as async task
        task_processor = await get_task_processor()
        task_id = await task_processor.submit_task(
            f"batch_meal_analysis_{len(request.meal_requests)}_meals",
            run_batch_workflow,
            priority=TaskPriority.NORMAL
        )

        return WorkflowStatusResponse(
            workflow_id=task_id,
            status="started",
            created_at=__import__('time').time(),
            updated_at=__import__('time').time()
        )

    except Exception as e:
        logger.error(
            f"Failed to start batch meal analysis workflow: {e}", exc_info=True)
        return workflow_error_response(e, "batch_meal_analysis")


@router.post("/insights/weekly", response_model=WorkflowStatusResponse)
async def start_weekly_insights_workflow(
    request: WeeklyInsightsRequest,
    background_tasks: BackgroundTasks,
    current_user: Student = Depends(get_current_user)
):
    """
    Start a weekly insights generation workflow.

    Analyzes the user's meal history for the past week and generates
    nutritional insights and recommendations.
    """
    try:
        orchestrator = get_orchestrator()
        meal_workflow = MealAnalysisWorkflow(orchestrator)

        # Start the insights workflow asynchronously
        async def run_insights_workflow():
            try:
                result = await meal_workflow.generate_weekly_insights(
                    student_id=str(current_user.student_id),
                    week_start=request.week_start
                )
                logger.info(
                    f"Weekly insights generation completed for user {current_user.student_id}")
                return result
            except Exception as e:
                logger.error(
                    f"Weekly insights workflow failed for user {current_user.student_id}: {e}", exc_info=True)
                raise

        # Submit as async task
        task_processor = await get_task_processor()
        task_id = await task_processor.submit_task(
            f"weekly_insights_{current_user.student_id}",
            run_insights_workflow,
            priority=TaskPriority.NORMAL
        )

        return WorkflowStatusResponse(
            workflow_id=task_id,
            status="started",
            created_at=__import__('time').time(),
            updated_at=__import__('time').time()
        )

    except Exception as e:
        logger.error(
            f"Failed to start weekly insights workflow: {e}", exc_info=True)
        return workflow_error_response(e, "weekly_insights")


@router.get("/status/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str,
    current_user: Student = Depends(get_current_user)
):
    """
    Get the status of a running or completed workflow.

    Returns the current status, progress information, and results if available.
    """
    try:
        task_processor = await get_task_processor()
        task_status = await task_processor.get_task_status(workflow_id)

        if task_status is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )

        return WorkflowStatusResponse(
            workflow_id=workflow_id,
            status=task_status["status"],
            result=task_status.get("result"),
            error=task_status.get("error"),
            created_at=task_status["created_at"],
            updated_at=task_status.get("completed_at") or task_status.get(
                "started_at") or task_status["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get workflow status for {workflow_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow status"
        )


@router.delete("/cancel/{workflow_id}")
async def cancel_workflow(
    workflow_id: str,
    current_user: Student = Depends(get_current_user)
):
    """
    Cancel a running workflow.

    Attempts to cancel the specified workflow if it's still running.
    """
    try:
        task_processor = await get_task_processor()
        cancelled = await task_processor.cancel_task(workflow_id)

        if not cancelled:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found or cannot be cancelled"
            )

        return {
            "message": f"Workflow {workflow_id} cancelled successfully",
            "workflow_id": workflow_id,
            "timestamp": __import__('time').time()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to cancel workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel workflow"
        )


@router.get("/list")
async def list_user_workflows(
    current_user: Student = Depends(get_current_user),
    status_filter: Optional[str] = None,
    limit: int = 50
):
    """
    List workflows for the current user.

    Returns a list of workflows initiated by the current user with optional filtering.
    """
    try:
        task_processor = await get_task_processor()

        # Get all task stats (this is a simplified implementation)
        # In a production system, you'd want to filter by user and implement proper pagination
        stats = await task_processor.get_queue_stats()

        # This is a placeholder - in a real implementation, you'd need to:
        # 1. Store user associations with tasks
        # 2. Implement proper filtering and pagination
        # 3. Return actual user-specific workflows

        return {
            "workflows": [],  # Placeholder
            "total": 0,
            "limit": limit,
            "status_filter": status_filter,
            "message": "Workflow listing not fully implemented - requires user-task association tracking"
        }

    except Exception as e:
        logger.error(
            f"Failed to list workflows for user {current_user.student_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow list"
        )


@router.get("/stats")
async def get_workflow_statistics(
    current_user: Student = Depends(get_current_user)
):
    """
    Get workflow statistics and system performance metrics.

    Returns information about workflow execution, queue status, and performance.
    """
    try:
        # Get task processor stats
        task_processor = await get_task_processor()
        task_stats = await task_processor.get_queue_stats()

        # Get orchestrator stats
        orchestrator = get_orchestrator()
        orchestrator_stats = {
            "running_workflows": len(orchestrator.running_tasks),
            "completed_workflows": len(orchestrator.task_results),
            "max_concurrent": orchestrator.max_concurrent_tasks
        }

        return {
            "task_processor": task_stats,
            "orchestrator": orchestrator_stats,
            "timestamp": __import__('time').time(),
            "service": "workflow-orchestration"
        }

    except Exception as e:
        logger.error(f"Failed to get workflow statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow statistics"
        )
