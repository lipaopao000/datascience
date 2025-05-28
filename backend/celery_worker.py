import os
from celery import Celery
from backend.core.config import settings

# Set the default Django settings module for the 'celery' program.
# This is not strictly necessary if not using Django, but helps Celery find app config.
# We can point it to our FastAPI app's config module.
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings') # Example if Django
# For FastAPI, we directly use our settings object.

# Create Celery application instance
# The first argument is the name of the current module, used for naming tasks.
# The second argument `broker` specifies the URL of the message broker.
# The third argument `backend` specifies the URL of the result backend.
celery_app = Celery(
    "datascience_ml_worker", # A name for this Celery app
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['backend.tasks']  # List of modules to import when the worker starts.
                               # We will create backend/tasks.py for our tasks.
)

# Optional configuration, see the Celery documentation for more details.
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Ignore other content
    result_serializer='json',
    timezone='UTC', # Or your project's timezone, e.g., settings.TIMEZONE
    enable_utc=True,
    # For long-running tasks, it might be better to acknowledge only after completion.
    task_acks_late=True,
    # If a worker process is killed, requeue the task.
    task_reject_on_worker_lost=True,
    # Track when tasks are started by workers
    task_track_started=True,
    # Configure Celery to look for settings with the 'CELERY_' prefix in our settings object
    # This is not directly used here as we pass broker/backend URLs explicitly,
    # but good for other Celery settings if defined in config.py (e.g., CELERY_TASK_ROUTES)
    # celery_app.config_from_object(settings, namespace='CELERY')
)


# Example of how to load task modules if not using `include` in Celery constructor
# celery_app.autodiscover_tasks(lambda: settings.INSTALLED_APPS) # Django style
# For FastAPI, if tasks are in `backend.tasks`, the `include` parameter is usually sufficient.

if __name__ == '__main__':
    # This is for running the worker directly using `python backend/celery_worker.py worker -l info`
    # Ensure that the paths are set up correctly for imports if run this way.
    # It's common to run celery worker from the project root:
    # `celery -A backend.celery_worker worker -l info -Q myqueue` (if using queues)
    
    # To run the worker, you'd typically use the command line:
    # celery -A backend.celery_worker.celery_app worker -l INFO
    # or if your celery_app instance is named 'app':
    # celery -A backend.celery_worker.app worker -l INFO

    # The following lines are not standard for running a worker but can be used for direct script execution tests.
    # For actual worker execution, use the Celery CLI.
    print("Celery worker script. To run the worker, use the Celery CLI:")
    print("Example: celery -A backend.celery_worker.celery_app worker -l INFO")
    # celery_app.start() # This is not how you typically start a worker.
