"""Async task processing for long-running operations."""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import time
import uuid
import json
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AsyncTask:
    """Async task definition."""
    task_id: str
    name: str
    func: Callable[..., Awaitable[Any]]
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0


class AsyncTaskProcessor:
    """Processes async tasks with queue management and retry logic."""

    def __init__(self, max_workers: int = 5, max_queue_size: int = 100):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue(
            maxsize=max_queue_size)
        self.active_tasks: Dict[str, AsyncTask] = {}
        self.completed_tasks: Dict[str, AsyncTask] = {}
        self.workers: List[asyncio.Task] = []
        self.running = False
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)

    async def start(self):
        """Start the task processor workers."""
        if self.running:
            return

        self.running = True
        logger.info(
            f"Starting async task processor with {self.max_workers} workers")

        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)

    async def stop(self):
        """Stop the task processor and cleanup."""
        if not self.running:
            return

        logger.info("Stopping async task processor")
        self.running = False

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)

        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)

        self.workers.clear()
        logger.info("Async task processor stopped")

    async def submit_task(
        self,
        name: str,
        func: Callable[..., Awaitable[Any]],
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Submit a task for async processing.

        Returns:
            Task ID for tracking
        """
        task_id = str(uuid.uuid4())

        task = AsyncTask(
            task_id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout
        )

        # Add to queue with priority (lower number = higher priority)
        priority_value = 5 - priority.value  # Invert for queue ordering
        await self.task_queue.put((priority_value, time.time(), task))

        logger.info(f"Submitted task '{name}' with ID {task_id}")
        return task_id

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a task."""
        # Check active tasks
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return self._task_to_dict(task)

        # Check completed tasks
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            return self._task_to_dict(task)

        return None

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or active task."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = "cancelled"
            task.completed_at = time.time()

            # Move to completed tasks
            self.completed_tasks[task_id] = task
            del self.active_tasks[task_id]

            logger.info(f"Cancelled task {task_id}")
            return True

        return False

    async def _worker(self, worker_name: str):
        """Worker coroutine that processes tasks from the queue."""
        logger.info(f"Worker {worker_name} started")

        while self.running:
            try:
                # Get task from queue with timeout
                try:
                    priority, timestamp, task = await asyncio.wait_for(
                        self.task_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Process the task
                await self._process_task(task, worker_name)

            except asyncio.CancelledError:
                logger.info(f"Worker {worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}", exc_info=True)

        logger.info(f"Worker {worker_name} stopped")

    async def _process_task(self, task: AsyncTask, worker_name: str):
        """Process a single task."""
        logger.info(
            f"Worker {worker_name} processing task {task.task_id}: {task.name}")

        # Move to active tasks
        self.active_tasks[task.task_id] = task
        task.status = "running"
        task.started_at = time.time()

        try:
            # Execute task with timeout
            if task.timeout:
                result = await asyncio.wait_for(
                    task.func(*task.args, **task.kwargs),
                    timeout=task.timeout
                )
            else:
                result = await task.func(*task.args, **task.kwargs)

            # Task completed successfully
            task.status = "completed"
            task.result = result
            task.completed_at = time.time()

            logger.info(
                f"Task {task.task_id} completed successfully in "
                f"{task.completed_at - task.started_at:.2f}s"
            )

        except asyncio.TimeoutError:
            logger.error(
                f"Task {task.task_id} timed out after {task.timeout}s")
            await self._handle_task_failure(task, "Task timed out")

        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}", exc_info=True)
            await self._handle_task_failure(task, str(e))

        finally:
            # Move to completed tasks
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
            self.completed_tasks[task.task_id] = task

    async def _handle_task_failure(self, task: AsyncTask, error_message: str):
        """Handle task failure with retry logic."""
        task.error = error_message
        task.retry_count += 1

        if task.retry_count <= task.max_retries:
            logger.info(
                f"Retrying task {task.task_id} (attempt {task.retry_count}/{task.max_retries}) "
                f"after {task.retry_delay}s delay"
            )

            # Reset task status for retry
            task.status = "retrying"
            task.started_at = None

            # Schedule retry after delay
            await asyncio.sleep(task.retry_delay)

            # Re-queue the task
            priority_value = 5 - task.priority.value
            await self.task_queue.put((priority_value, time.time(), task))
        else:
            logger.error(
                f"Task {task.task_id} failed permanently after {task.retry_count} attempts"
            )
            task.status = "failed"
            task.completed_at = time.time()

    def _task_to_dict(self, task: AsyncTask) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            "task_id": task.task_id,
            "name": task.name,
            "status": task.status,
            "priority": task.priority.name,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "error": task.error,
            "result": task.result if task.status == "completed" else None
        }

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue and processing statistics."""
        return {
            "queue_size": self.task_queue.qsize(),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "workers": len(self.workers),
            "running": self.running,
            "max_workers": self.max_workers,
            "max_queue_size": self.max_queue_size
        }

    async def cleanup_completed_tasks(self, max_age_seconds: int = 3600):
        """Clean up old completed tasks."""
        current_time = time.time()
        to_remove = []

        for task_id, task in self.completed_tasks.items():
            if (task.completed_at and
                    current_time - task.completed_at > max_age_seconds):
                to_remove.append(task_id)

        for task_id in to_remove:
            del self.completed_tasks[task_id]

        logger.info(f"Cleaned up {len(to_remove)} old completed tasks")


# Global task processor instance
_task_processor = None


async def get_task_processor() -> AsyncTaskProcessor:
    """Get the global task processor instance."""
    global _task_processor
    if _task_processor is None:
        _task_processor = AsyncTaskProcessor(
            max_workers=settings.MAX_CONCURRENT_REQUESTS,
            max_queue_size=100
        )
        await _task_processor.start()
    return _task_processor


async def submit_async_task(
    name: str,
    func: Callable[..., Awaitable[Any]],
    *args,
    priority: TaskPriority = TaskPriority.NORMAL,
    **kwargs
) -> str:
    """Convenience function to submit an async task."""
    processor = await get_task_processor()
    return await processor.submit_task(name, func, *args, priority=priority, **kwargs)


# Common async task functions for the nutrition feedback system

async def async_meal_analysis(meal_id: str, image_path: str) -> Dict[str, Any]:
    """Async meal analysis task."""
    logger.info(f"Starting async meal analysis for meal {meal_id}")

    # Simulate long-running analysis
    await asyncio.sleep(2.0)

    return {
        "meal_id": meal_id,
        "detected_foods": ["jollof_rice", "chicken", "plantain"],
        "confidence_scores": [0.95, 0.88, 0.92],
        "analysis_complete": True,
        "timestamp": time.time()
    }


async def async_weekly_insights_generation(student_id: str) -> Dict[str, Any]:
    """Async weekly insights generation task."""
    logger.info(f"Generating weekly insights for student {student_id}")

    # Simulate insights generation
    await asyncio.sleep(3.0)

    return {
        "student_id": student_id,
        "week_period": "2024-01-01 to 2024-01-07",
        "nutrition_balance": {
            "carbohydrates": 0.8,
            "proteins": 0.6,
            "vegetables": 0.4
        },
        "recommendations": [
            "Try to include more vegetables in your meals",
            "Good protein intake this week!"
        ],
        "generated_at": time.time()
    }


async def async_model_training(dataset_path: str, model_config: Dict[str, Any]) -> Dict[str, Any]:
    """Async model training task."""
    logger.info(f"Starting model training with dataset {dataset_path}")

    # Simulate model training (this would be much longer in reality)
    await asyncio.sleep(5.0)

    return {
        "model_path": "models/trained_model.pth",
        "accuracy": 0.94,
        "training_time": 5.0,
        "dataset_size": 1000,
        "completed_at": time.time()
    }
