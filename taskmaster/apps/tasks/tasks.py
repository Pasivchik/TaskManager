from celery import shared_task

from .services import generate_due_repeated_tasks


@shared_task(name='apps.tasks.tasks.generate_repeated_tasks')
def generate_repeated_tasks():
    return generate_due_repeated_tasks()
