from fastapi import APIRouter, Depends, HTTPException, status
from celery.result import AsyncResult
from typing import Any

from backend.celery_worker import celery_app # Import the celery_app instance
from backend.tasks import long_running_ml_task, add # Import specific tasks
from backend.core.security import get_current_active_user # For securing endpoints
from backend.models import schemas # For request/response models if needed

router = APIRouter()

@router.post("/trigger-ml-task", status_code=status.HTTP_202_ACCEPTED, response_model=schemas.TaskStatusResponse)
async def trigger_ml_task_endpoint(
    project_id: int, # Example parameter, adjust as needed
    data_path: str = "/fake/path/to/data.csv", # Example parameter
    # current_user: models.User = Depends(get_current_active_user) # Uncomment to secure
):
    """
    Triggers the placeholder long-running ML task.
    """
    # In a real scenario, you'd get project_id, data_path, model_params from request body or path
    model_params = {"learning_rate": 0.01, "epochs": 100}
    
    task = long_running_ml_task.delay(project_id=project_id, data_path=data_path, model_params=model_params)
    return {"task_id": task.id, "status": "PENDING", "message": "ML task has been submitted."}

@router.post("/trigger-add-task", status_code=status.HTTP_202_ACCEPTED, response_model=schemas.TaskStatusResponse)
async def trigger_add_task_endpoint(
    x: int = 5,
    y: int = 10,
    # current_user: models.User = Depends(get_current_active_user) # Uncomment to secure
):
    """
    Triggers the simple add task.
    """
    task = add.delay(x, y)
    return {"task_id": task.id, "status": "PENDING", "message": "Add task has been submitted."}


@router.get("/task-status/{task_id}", response_model=schemas.TaskStatusResponse)
async def get_task_status_endpoint(
    task_id: str,
    # current_user: models.User = Depends(get_current_active_user) # Uncomment to secure
):
    """
    Retrieves the status and result of a Celery task.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    
    response_data = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None,
        "message": ""
    }

    if task_result.status == 'PENDING':
        response_data["message"] = "Task is pending or has not started yet."
    elif task_result.status == 'STARTED':
        response_data["message"] = "Task has started."
        if task_result.info: # If task provides meta during PROGRESS
             response_data["meta"] = task_result.info
    elif task_result.status == 'SUCCESS':
        response_data["message"] = "Task completed successfully."
    elif task_result.status == 'FAILURE':
        response_data["message"] = "Task failed."
        # task_result.result will contain the exception if it failed
        # Be careful about exposing raw exception details to the client
        response_data["result"] = str(task_result.result) # Or a more generic error message
        if task_result.info: # If task provides meta during FAILURE
             response_data["meta"] = task_result.info
    elif task_result.status == 'RETRY':
        response_data["message"] = "Task is being retried."
    elif task_result.status == 'REVOKED':
        response_data["message"] = "Task was revoked."
    else: # PROGRESS or custom states
        response_data["message"] = f"Task is in status: {task_result.status}."
        if task_result.info: # If task provides meta during PROGRESS
             response_data["meta"] = task_result.info
             
    return response_data

# Note: The `schemas.TaskStatusResponse` needs to be defined in `backend/models/schemas.py`.
# It should include fields like task_id, status, result (optional), message (optional), meta (optional).
