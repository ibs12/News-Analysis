# celery_config.py
from celery import Celery
from celery.schedules import crontab
import multiprocessing

# Set the start method to 'spawn'
try:
    multiprocessing.set_start_method('spawn')
except RuntimeError:
    pass

def make_celery(app=None):
    if app is None:
        from app import app  # Avoid circular imports

    celery = Celery(
        app.import_name,
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0'
    )
    
    # Base configuration
    celery.conf.update(app.config)
    
    # Performance and reliability configurations
    celery.conf.update({
        'task_acks_late': True,
        'worker_prefetch_multiplier': 1,
        'worker_max_tasks_per_child': 1,  # Reduce this to prevent memory issues
        'worker_concurrency': 1,  # Limit to one worker process
    })

    # Beat schedule configuration
    celery.conf.beat_schedule = {
        'fetch-every-15-minutes': {
            'task': 'tasks.fetch_data',
            'schedule': 900.0,
        },
    }

    # Import tasks to ensure they are registered
    with app.app_context():
        import tasks

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery