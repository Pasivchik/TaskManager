"""
Команда для настройки расписания Celery Beat.
Запускать один раз после деплоя: python manage.py setup_periodic_tasks
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json


class Command(BaseCommand):
    help = 'Настройка периодических задач Celery Beat'

    def handle(self, *args, **options):
        # 00:05 каждую ночь — сброс стриков
        midnight_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='5',
            hour='0',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

        # 20:00 каждый день — напоминания
        evening_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='20',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

        # 00:10 каждый день — генерация повторяющихся задач
        repeated_tasks_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='10',
            hour='0',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

        # Создаём или обновляем задачи
        task1, created = PeriodicTask.objects.update_or_create(
            name='Сброс стриков (ежедневно 00:05)',
            defaults={
                'crontab': midnight_schedule,
                'task': 'apps.gamification.tasks.reset_streaks',
                'args': json.dumps([]),
                'enabled': True,
            }
        )

        task_repeats, created_repeats = PeriodicTask.objects.update_or_create(
            name='Генерация повторяющихся задач (ежедневно 00:10)',
            defaults={
                'crontab': repeated_tasks_schedule,
                'task': 'apps.tasks.tasks.generate_repeated_tasks',
                'args': json.dumps([]),
                'enabled': True,
            }
        )

        task2, created2 = PeriodicTask.objects.update_or_create(
            name='Напоминания пользователям (ежедневно 20:00)',
            defaults={
                'crontab': evening_schedule,
                'task': 'apps.gamification.tasks.send_reminders',
                'args': json.dumps([]),
                'enabled': True,
            }
        )

        self.stdout.write(self.style.SUCCESS('✓ Периодические задачи настроены:'))
        self.stdout.write(f'  • Сброс стриков: каждый день в 00:05')
        self.stdout.write(f'  • Повторяющиеся задачи: каждый день в 00:10')
        self.stdout.write(f'  • Напоминания: каждый день в 20:00')
