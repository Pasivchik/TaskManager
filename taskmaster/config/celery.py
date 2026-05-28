import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('taskmaster')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Периодические задачи
app.conf.beat_schedule = {
    # Сброс стрика — каждую ночь в 00:05
    'reset-streaks-daily': {
        'task': 'apps.gamification.tasks.reset_streaks',
        'schedule': crontab(hour=0, minute=5),
    },
    # Генерация ежедневных, повторяющихся и долгосрочных задач
    'generate-repeated-tasks-daily': {
        'task': 'apps.tasks.tasks.generate_repeated_tasks',
        'schedule': crontab(hour=0, minute=10),
    },
    # Напоминания — каждый день в 20:00
    'send-reminders-daily': {
        'task': 'apps.gamification.tasks.send_reminders',
        'schedule': crontab(hour=20, minute=0),
    },
}
