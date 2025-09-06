# Service Orchestration and Coordination Implementation

## Overview

This document summarizes the implementation of task 8.2 "Implement service orchestration and coordination" for the nutrition feedback system.

## Components Implemented

### 1. Enhanced Service Orchestration Layer (`app/core/orchestration.py`)

**Key Features:**
- **ServiceOrchestrator**: Coordinates complex workflows across multiple services
- **MealAnalysisWorkflow**: Specific workflows for meal analysis and insights generation
- **WorkflowError**: Custom exception handling for workflow failures
- **Real Service Integration**: Actual routing to image, inference, feedback, history, and user services
- **Error Recovery**: Support for optional vs required workflow steps
- **Timeout Handling**: Per-step timeout configuration
- **Parallel Execution**: Batch processing with concurrency control

**Workflows Implemented:**
- Complete meal analysis (image → ML inference → feedback → history)
- Weekly insights generation
- Batch meal analysis processing
- Model retraining coordination

### 2. Async Task Processing (`app/core/async_tasks.py`)

**Key Features:**
- **AsyncTaskProcessor**: Queue-based task processing with worker pools
- **Priority System**: HIGH, NORMAL, LOW, CRITICAL priority levels
- **Retry Logic**: Configurable retry attempts with exponential backoff
- **Timeout Support**: Per-task timeout configuration
- **Concurrency Control**: Semaphore-based worker management
- **Task Tracking**: Complete lifecycle tracking (pending → running → completed/failed)
- **Cleanup**: Automatic cleanup of old completed tasks

**Task Types:**
- Long-running ML model inference
- Weekly insights generation
- Model training operations
- Batch processing jobs

### 3. Comprehensive Health Checks (`app/core/health_checks.py`)

**Health Check Categories:**
- **Database**: Connection, query performance, response times
- **System Resources**: Memory usage, CPU utilization, disk space
- **File System**: Upload directory access, read/write permissions
- **ML Models**: Model file availability and integrity
- **Async Tasks**: Queue status and worker health
- **Overall Status**: Aggregated health assessment

**Status Levels:**
- `HEALTHY`: All systems operating normally
- `DEGRADED`: Some issues but service still functional
- `UNHEALTHY`: Critical issues requiring attention

### 4. Standardized Error Handling (`app/core/error_handling.py`)

**Error Categories:**
- Validation errors (422)
- Authentication/Authorization (401/403)
- Not Found (404)
- Rate Limiting (429)
- Service Unavailable (503)
- Internal Errors (500)
- Workflow Errors
- ML Processing Errors
- Storage Errors

**Error Response Format:**
```json
{
  "error": {
    "category": "validation",
    "code": "VALIDATION_FAILED",
    "message": "Request validation failed",
    "timestamp": 1234567890.123,
    "details": [...],
    "request_id": "req-123",
    "user_message": "Please check your input and try again"
  }
}
```

### 5. Monitoring and Metrics Endpoints (`app/api/v1/endpoints/monitoring.py`)

**Endpoints:**
- `GET /monitoring/health` - Comprehensive health check
- `GET /monitoring/health/{check_name}` - Specific health check
- `GET /monitoring/metrics` - System performance metrics
- `GET /monitoring/tasks/status` - Task queue statistics
- `GET /monitoring/tasks/{task_id}` - Individual task status
- `DELETE /monitoring/tasks/{task_id}` - Cancel running task
- `POST /monitoring/maintenance/cleanup` - Clean old data
- `GET /monitoring/ping` - Basic availability check
- `GET /monitoring/ready` - Readiness probe for containers

### 6. Workflow API Endpoints (`app/api/v1/endpoints/workflows.py`)

**Endpoints:**
- `POST /workflows/meals/analyze` - Start meal analysis workflow
- `POST /workflows/meals/analyze/batch` - Batch meal analysis
- `POST /workflows/insights/weekly` - Generate weekly insights
- `GET /workflows/status/{workflow_id}` - Get workflow status
- `DELETE /workflows/cancel/{workflow_id}` - Cancel workflow
- `GET /workflows/list` - List user workflows
- `GET /workflows/stats` - Workflow statistics

### 7. End-to-End Tests (`tests/test_end_to_end_workflows.py`)

**Test Coverage:**
- Complete meal analysis workflow
- Workflow failure recovery (optional vs required steps)
- Weekly insights generation
- Batch processing
- Async task integration
- API error handling
- Health check integration
- Metrics endpoints
- Concurrent request handling
- Timeout handling
- Request ID propagation

## Integration Points

### Application Startup
- Async task processor initialization
- Service orchestrator setup
- Health check system activation
- Proper cleanup on shutdown

### Error Handling Integration
- Global exception handlers use standardized error responses
- Request ID propagation through error responses
- Workflow-specific error handling

### Service Dependencies
- Image Service integration
- ML Inference Service integration
- Feedback Service integration
- History Service integration
- User Service integration

## Performance Characteristics

### Concurrency
- Configurable worker pools for async tasks
- Semaphore-based concurrency control
- Parallel workflow execution support

### Scalability
- Queue-based task processing
- Horizontal scaling support
- Resource usage monitoring

### Reliability
- Retry logic with exponential backoff
- Graceful degradation for optional steps
- Comprehensive error recovery

## Configuration

### Environment Variables
- `MAX_CONCURRENT_REQUESTS`: Maximum concurrent task workers
- `UPLOAD_DIR`: File upload directory for health checks
- `MODEL_PATH`: ML model file path
- `FOOD_MAPPING_PATH`: Food classification mapping file

### Timeouts
- Default workflow step timeout: 30 seconds
- ML inference timeout: 60 seconds
- Model training timeout: 3600 seconds (1 hour)

## Monitoring and Observability

### Metrics Collected
- Task queue size and processing times
- Workflow success/failure rates
- System resource utilization
- API response times
- Error rates by category

### Health Monitoring
- Automated health checks every request
- Degraded service detection
- Critical issue alerting
- Resource threshold monitoring

## Requirements Satisfied

✅ **Requirement 2.1**: ML processing coordination and workflow management
✅ **Requirement 8.2**: Scalable backend architecture with proper orchestration

## Usage Examples

### Starting a Meal Analysis Workflow
```python
# Via API
POST /api/v1/workflows/meals/analyze
{
  "meal_id": "meal_123",
  "image_path": "/uploads/meal_image.jpg"
}

# Programmatically
orchestrator = get_orchestrator()
workflow = MealAnalysisWorkflow(orchestrator)
result = await workflow.analyze_meal_complete(
    student_id="user_123",
    meal_id="meal_123", 
    image_path="/uploads/meal_image.jpg"
)
```

### Monitoring System Health
```python
# Check overall health
GET /api/v1/monitoring/health

# Check specific component
GET /api/v1/monitoring/health/database

# Get system metrics
GET /api/v1/monitoring/metrics
```

### Async Task Processing
```python
processor = await get_task_processor()
task_id = await processor.submit_task(
    "long_running_analysis",
    analyze_function,
    data,
    priority=TaskPriority.HIGH,
    timeout=300
)
```

## Future Enhancements

1. **Distributed Processing**: Redis-based task queue for multi-instance deployment
2. **Advanced Metrics**: Prometheus integration for detailed monitoring
3. **Workflow Visualization**: Real-time workflow execution dashboards
4. **Auto-scaling**: Dynamic worker pool scaling based on queue size
5. **Circuit Breakers**: Automatic service failure detection and recovery