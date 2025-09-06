"""Service orchestration and coordination layer."""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import time
import uuid
from contextlib import asynccontextmanager

from app.core.config import settings

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    """Task execution result."""
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def duration(self) -> Optional[float]:
        """Get task execution duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


class ServiceOrchestrator:
    """Coordinates complex workflows across multiple services."""

    def __init__(self):
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, TaskResult] = {}
        self.max_concurrent_tasks = settings.MAX_CONCURRENT_REQUESTS
        self._semaphore = asyncio.Semaphore(self.max_concurrent_tasks)

    async def execute_workflow(
        self,
        workflow_name: str,
        steps: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> TaskResult:
        """
        Execute a multi-step workflow.

        Args:
            workflow_name: Name of the workflow
            steps: List of workflow steps with service calls
            context: Shared context data between steps

        Returns:
            TaskResult with workflow execution result
        """
        task_id = str(uuid.uuid4())
        context = context or {}

        logger.info(
            f"Starting workflow '{workflow_name}' with task_id: {task_id}")

        result = TaskResult(
            task_id=task_id,
            status=TaskStatus.PENDING,
            start_time=time.time()
        )

        self.task_results[task_id] = result

        try:
            result.status = TaskStatus.RUNNING

            # Execute workflow steps sequentially
            workflow_result = {}
            for i, step in enumerate(steps):
                step_name = step.get("name", f"step_{i}")
                service_name = step.get("service")
                method_name = step.get("method")
                params = step.get("params", {})
                required = step.get("required", True)
                retry_on_failure = step.get("retry_on_failure", False)
                step_timeout = step.get("timeout")

                logger.info(
                    f"Executing step '{step_name}' in workflow '{workflow_name}' "
                    f"(required: {required}, retry: {retry_on_failure})"
                )

                # Merge context into params
                step_params = {**params, **context}

                try:
                    # Execute step with optional timeout
                    if step_timeout:
                        step_result = await asyncio.wait_for(
                            self._execute_service_call(
                                service_name, method_name, step_params),
                            timeout=step_timeout
                        )
                    else:
                        step_result = await self._execute_service_call(
                            service_name, method_name, step_params
                        )

                    # Store step result in context for next steps
                    context[f"{step_name}_result"] = step_result
                    workflow_result[step_name] = step_result

                    logger.info(
                        f"Completed step '{step_name}' in workflow '{workflow_name}'"
                    )

                except Exception as step_error:
                    logger.error(
                        f"Step '{step_name}' failed in workflow '{workflow_name}': {step_error}",
                        exc_info=True
                    )

                    # Handle step failure based on requirements
                    if required:
                        # Required step failed - fail the entire workflow
                        raise WorkflowError(
                            f"Required step '{step_name}' failed: {step_error}",
                            step_name=step_name,
                            original_error=step_error
                        )
                    else:
                        # Optional step failed - log and continue
                        logger.warning(
                            f"Optional step '{step_name}' failed, continuing workflow: {step_error}"
                        )
                        workflow_result[step_name] = {
                            "status": "failed",
                            "error": str(step_error),
                            "optional": True
                        }

            result.status = TaskStatus.COMPLETED
            result.result = workflow_result

        except Exception as e:
            logger.error(
                f"Workflow '{workflow_name}' failed: {e}", exc_info=True)
            result.status = TaskStatus.FAILED
            result.error = str(e)

        finally:
            result.end_time = time.time()
            logger.info(
                f"Workflow '{workflow_name}' finished with status {result.status.value} "
                f"in {result.duration:.2f}s"
            )

        return result

    async def execute_parallel_tasks(
        self,
        tasks: List[Dict[str, Any]],
        max_concurrent: Optional[int] = None
    ) -> List[TaskResult]:
        """
        Execute multiple tasks in parallel with concurrency control.

        Args:
            tasks: List of task definitions
            max_concurrent: Maximum concurrent tasks (defaults to system limit)

        Returns:
            List of TaskResult objects
        """
        max_concurrent = max_concurrent or self.max_concurrent_tasks
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_single_task(task_def: Dict[str, Any]) -> TaskResult:
            async with semaphore:
                task_id = str(uuid.uuid4())
                result = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.RUNNING,
                    start_time=time.time()
                )

                try:
                    service_name = task_def.get("service")
                    method_name = task_def.get("method")
                    params = task_def.get("params", {})

                    task_result = await self._execute_service_call(
                        service_name, method_name, params
                    )

                    result.status = TaskStatus.COMPLETED
                    result.result = task_result

                except Exception as e:
                    logger.error(
                        f"Parallel task {task_id} failed: {e}", exc_info=True)
                    result.status = TaskStatus.FAILED
                    result.error = str(e)

                finally:
                    result.end_time = time.time()

                return result

        # Execute all tasks in parallel
        task_coroutines = [execute_single_task(task) for task in tasks]
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)

        # Handle any exceptions that occurred
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = TaskResult(
                    task_id=str(uuid.uuid4()),
                    status=TaskStatus.FAILED,
                    error=str(result),
                    start_time=time.time(),
                    end_time=time.time()
                )
                final_results.append(error_result)
            else:
                final_results.append(result)

        return final_results

    async def _execute_service_call(
        self,
        service_name: str,
        method_name: str,
        params: Dict[str, Any]
    ) -> Any:
        """Execute a service method call with actual service integration."""
        logger.info(
            f"Executing {service_name}.{method_name} with params: {params}")

        try:
            # Route to appropriate service based on service_name
            if service_name == "image_service":
                return await self._call_image_service(method_name, params)
            elif service_name == "inference_service":
                return await self._call_inference_service(method_name, params)
            elif service_name == "feedback_service":
                return await self._call_feedback_service(method_name, params)
            elif service_name == "history_service":
                return await self._call_history_service(method_name, params)
            elif service_name == "insights_service":
                return await self._call_insights_service(method_name, params)
            elif service_name == "user_service":
                return await self._call_user_service(method_name, params)
            else:
                raise ValueError(f"Unknown service: {service_name}")

        except Exception as e:
            logger.error(
                f"Service call failed: {service_name}.{method_name} - {e}", exc_info=True)
            raise

    async def _call_image_service(self, method_name: str, params: Dict[str, Any]) -> Any:
        """Call image service methods."""
        from app.services.image_service import ImageService

        service = ImageService()

        if method_name == "preprocess_image":
            return await service.preprocess_image(
                params["image_path"],
                params.get("meal_id")
            )
        elif method_name == "validate_image":
            return await service.validate_image(params["image_path"])
        elif method_name == "store_image":
            return await service.store_image(
                params["image_data"],
                params.get("metadata", {})
            )
        else:
            raise ValueError(f"Unknown image service method: {method_name}")

    async def _call_inference_service(self, method_name: str, params: Dict[str, Any]) -> Any:
        """Call ML inference service methods."""
        from app.ml.inference.predictor import FoodPredictor

        predictor = FoodPredictor()

        if method_name == "analyze_food":
            return await predictor.predict_food_async(
                params.get("image_path") or params.get("meal_id")
            )
        elif method_name == "batch_analyze":
            return await predictor.batch_predict_async(params["image_paths"])
        else:
            raise ValueError(
                f"Unknown inference service method: {method_name}")

    async def _call_feedback_service(self, method_name: str, params: Dict[str, Any]) -> Any:
        """Call feedback service methods."""
        from app.services.feedback_service import FeedbackService

        service = FeedbackService()

        if method_name == "generate_feedback":
            return await service.generate_feedback_async(
                params["meal_id"],
                params.get("student_id")
            )
        elif method_name == "store_feedback":
            return await service.store_feedback(
                params["feedback_data"],
                params["meal_id"]
            )
        else:
            raise ValueError(f"Unknown feedback service method: {method_name}")

    async def _call_history_service(self, method_name: str, params: Dict[str, Any]) -> Any:
        """Call history service methods."""
        from app.services.history_service import HistoryService

        service = HistoryService()

        if method_name == "store_meal_record":
            return await service.store_meal_record_async(
                params["meal_id"],
                params["student_id"]
            )
        elif method_name == "get_weekly_meals":
            return await service.get_weekly_meals_async(params["student_id"])
        elif method_name == "store_weekly_insights":
            return await service.store_weekly_insights_async(
                params["student_id"],
                params.get("insights_data")
            )
        else:
            raise ValueError(f"Unknown history service method: {method_name}")

    async def _call_insights_service(self, method_name: str, params: Dict[str, Any]) -> Any:
        """Call insights service methods."""
        from app.services.insights_service import InsightsService

        service = InsightsService()

        if method_name == "analyze_nutrition_patterns":
            return await service.analyze_nutrition_patterns_async(params["student_id"])
        elif method_name == "generate_weekly_recommendations":
            return await service.generate_weekly_recommendations_async(params["student_id"])
        else:
            raise ValueError(f"Unknown insights service method: {method_name}")

    async def _call_user_service(self, method_name: str, params: Dict[str, Any]) -> Any:
        """Call user service methods."""
        from app.services.user_service import UserService

        service = UserService()

        if method_name == "validate_user":
            return await service.validate_user_async(params["student_id"])
        elif method_name == "update_preferences":
            return await service.update_preferences_async(
                params["student_id"],
                params["preferences"]
            )
        else:
            raise ValueError(f"Unknown user service method: {method_name}")

    async def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """Get the status of a running or completed task."""
        return self.task_results.get(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.cancel()

            if task_id in self.task_results:
                self.task_results[task_id].status = TaskStatus.CANCELLED
                self.task_results[task_id].end_time = time.time()

            return True
        return False

    def cleanup_completed_tasks(self, max_age_seconds: int = 3600):
        """Clean up old completed task results."""
        current_time = time.time()
        to_remove = []

        for task_id, result in self.task_results.items():
            if (result.end_time and
                current_time - result.end_time > max_age_seconds and
                    result.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]):
                to_remove.append(task_id)

        for task_id in to_remove:
            del self.task_results[task_id]
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

        logger.info(f"Cleaned up {len(to_remove)} old task results")


class WorkflowError(Exception):
    """Custom exception for workflow errors."""

    def __init__(self, message: str, step_name: str = None, original_error: Exception = None):
        self.step_name = step_name
        self.original_error = original_error
        super().__init__(message)


class MealAnalysisWorkflow:
    """Specific workflow for meal analysis coordination."""

    def __init__(self, orchestrator: ServiceOrchestrator):
        self.orchestrator = orchestrator

    async def analyze_meal_complete(
        self,
        student_id: str,
        meal_id: str,
        image_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> TaskResult:
        """
        Complete meal analysis workflow.

        This coordinates the entire process from image processing to feedback generation.
        """
        options = options or {}

        # Validate inputs
        if not all([student_id, meal_id, image_path]):
            raise WorkflowError(
                "Missing required parameters for meal analysis workflow")

        workflow_steps = [
            {
                "name": "validate_user",
                "service": "user_service",
                "method": "validate_user",
                "params": {"student_id": student_id},
                "required": True
            },
            {
                "name": "validate_image",
                "service": "image_service",
                "method": "validate_image",
                "params": {"image_path": image_path},
                "required": True
            },
            {
                "name": "preprocess_image",
                "service": "image_service",
                "method": "preprocess_image",
                "params": {"image_path": image_path, "meal_id": meal_id},
                "required": True
            },
            {
                "name": "recognize_food",
                "service": "inference_service",
                "method": "analyze_food",
                "params": {"meal_id": meal_id},
                "required": True,
                "retry_on_failure": True
            },
            {
                "name": "generate_feedback",
                "service": "feedback_service",
                "method": "generate_feedback",
                "params": {"meal_id": meal_id, "student_id": student_id},
                "required": True
            },
            {
                "name": "store_history",
                "service": "history_service",
                "method": "store_meal_record",
                "params": {"meal_id": meal_id, "student_id": student_id},
                "required": False  # Optional step - don't fail workflow if this fails
            }
        ]

        context = {
            "student_id": student_id,
            "meal_id": meal_id,
            "image_path": image_path,
            "workflow_options": options
        }

        return await self.orchestrator.execute_workflow(
            "meal_analysis_complete",
            workflow_steps,
            context
        )

    async def generate_weekly_insights(
        self,
        student_id: str,
        week_start: Optional[str] = None
    ) -> TaskResult:
        """Generate weekly insights workflow."""
        if not student_id:
            raise WorkflowError(
                "Missing student_id for weekly insights workflow")

        workflow_steps = [
            {
                "name": "validate_user",
                "service": "user_service",
                "method": "validate_user",
                "params": {"student_id": student_id},
                "required": True
            },
            {
                "name": "fetch_meal_history",
                "service": "history_service",
                "method": "get_weekly_meals",
                "params": {"student_id": student_id, "week_start": week_start},
                "required": True
            },
            {
                "name": "analyze_patterns",
                "service": "insights_service",
                "method": "analyze_nutrition_patterns",
                "params": {"student_id": student_id},
                "required": True
            },
            {
                "name": "generate_recommendations",
                "service": "insights_service",
                "method": "generate_weekly_recommendations",
                "params": {"student_id": student_id},
                "required": True
            },
            {
                "name": "store_insights",
                "service": "history_service",
                "method": "store_weekly_insights",
                "params": {"student_id": student_id},
                "required": False
            }
        ]

        context = {
            "student_id": student_id,
            "week_start": week_start
        }

        return await self.orchestrator.execute_workflow(
            "weekly_insights_generation",
            workflow_steps,
            context
        )

    async def batch_meal_analysis(
        self,
        meal_requests: List[Dict[str, str]]
    ) -> List[TaskResult]:
        """
        Process multiple meal analysis requests in parallel.

        Args:
            meal_requests: List of dicts with student_id, meal_id, image_path
        """
        if not meal_requests:
            return []

        # Create parallel tasks for each meal analysis
        tasks = []
        for request in meal_requests:
            task_def = {
                "service": "workflow",
                "method": "analyze_meal_complete",
                "params": request
            }
            tasks.append(task_def)

        # Execute in parallel with concurrency control
        return await self.orchestrator.execute_parallel_tasks(
            tasks,
            # Limit concurrent analyses
            max_concurrent=min(len(meal_requests), 5)
        )

    async def model_retraining_workflow(
        self,
        dataset_path: str,
        model_config: Dict[str, Any]
    ) -> TaskResult:
        """
        Coordinate model retraining workflow.

        This is a long-running workflow that should be executed asynchronously.
        """
        workflow_steps = [
            {
                "name": "validate_dataset",
                "service": "dataset_service",
                "method": "validate_dataset",
                "params": {"dataset_path": dataset_path},
                "required": True
            },
            {
                "name": "prepare_training_data",
                "service": "dataset_service",
                "method": "prepare_training_data",
                "params": {"dataset_path": dataset_path, "config": model_config},
                "required": True
            },
            {
                "name": "train_model",
                "service": "training_service",
                "method": "train_model",
                "params": {"config": model_config},
                "required": True,
                "timeout": 3600  # 1 hour timeout for training
            },
            {
                "name": "validate_model",
                "service": "training_service",
                "method": "validate_model",
                "params": {"model_config": model_config},
                "required": True
            },
            {
                "name": "deploy_model",
                "service": "inference_service",
                "method": "deploy_model",
                "params": {"model_config": model_config},
                "required": True
            }
        ]

        context = {
            "dataset_path": dataset_path,
            "model_config": model_config,
            "training_started_at": time.time()
        }

        return await self.orchestrator.execute_workflow(
            "model_retraining",
            workflow_steps,
            context
        )


# Global orchestrator instance
_orchestrator = None


def get_orchestrator() -> ServiceOrchestrator:
    """Get the global service orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ServiceOrchestrator()
    return _orchestrator


@asynccontextmanager
async def orchestrated_workflow(workflow_name: str):
    """Context manager for orchestrated workflows with cleanup."""
    orchestrator = get_orchestrator()
    start_time = time.time()

    logger.info(f"Starting orchestrated workflow: {workflow_name}")

    try:
        yield orchestrator
    except Exception as e:
        logger.error(f"Workflow {workflow_name} failed: {e}", exc_info=True)
        raise
    finally:
        duration = time.time() - start_time
        logger.info(f"Workflow {workflow_name} completed in {duration:.2f}s")

        # Cleanup old tasks periodically
        if len(orchestrator.task_results) > 100:
            orchestrator.cleanup_completed_tasks()
