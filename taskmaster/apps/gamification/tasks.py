from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(name='apps.gamification.tasks.reset_streaks')
def reset_streaks():
    """
    Запускается каждую ночь в 00:05.
    Сбрасывает streak пользователям, которые не были активны вчера.
    Если есть щит — тратит щит вместо сброса.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    today = timezone.now().date()
    yesterday = today - timezone.timedelta(days=1)

    # Пользователи у которых последняя активность — не вчера и не сегодня
    users_to_check = User.objects.filter(streak__gt=0).exclude(
        last_activity_date__gte=yesterday
    )

    reset_count = 0
    shield_used_count = 0

    for user in users_to_check:
        if user.streak_shields > 0:
            # Тратим щит, streak сохраняется
            user.streak_shields -= 1
            user.save(update_fields=['streak_shields'])
            shield_used_count += 1
            logger.info(f'Streak shield used for {user.username}. Shields left: {user.streak_shields}')
        else:
            # Сбрасываем streak
            user.streak = 0
            user.save(update_fields=['streak'])
            reset_count += 1
            logger.info(f'Streak reset for {user.username}')

    logger.info(f'Streak reset complete. Reset: {reset_count}, Shields used: {shield_used_count}')
    return {'reset': reset_count, 'shields_used': shield_used_count}


@shared_task(name='apps.gamification.tasks.send_reminders')
def send_reminders():
    """
    Запускается каждый день в 20:00.
    Отправляет email пользователям у которых есть незавершённые задачи на сегодня.
    """
    from django.contrib.auth import get_user_model
    from apps.tasks.models import Task
    from apps.tasks.services import generate_due_repeated_tasks

    User = get_user_model()
    today = timezone.now().date()
    generate_due_repeated_tasks(through_date=today)

    users_with_tasks = User.objects.filter(
        tasks__due_date=today,
        tasks__is_completed=False,
        email__isnull=False,
    ).distinct().exclude(email='')

    sent_count = 0

    for user in users_with_tasks:
        pending = Task.objects.filter(
            user=user,
            due_date=today,
            is_completed=False
        )
        pending_count = pending.count()

        if pending_count == 0:
            continue

        # Проверяем угрозу стрика
        streak_warning = ''
        if user.streak >= 3:
            activity_today = user.last_activity_date == today
            if not activity_today:
                streak_warning = (
                    f'\n⚠️ ВНИМАНИЕ: Твоя серия {user.streak} дней под угрозой!\n'
                    f'Выполни хотя бы одну задачу сегодня, чтобы её не потерять.\n'
                )

        subject = f'TaskMaster: у тебя {pending_count} незавершённых задач 📋'
        message = (
            f'Привет, {user.username}!\n\n'
            f'Сегодня {today.strftime("%d.%m.%Y")} у тебя осталось {pending_count} невыполненных задач:\n\n'
        )

        for task in pending[:5]:  # Показываем максимум 5
            message += f'  • {task.title} ({"⚡" * task.priority})\n'

        if pending_count > 5:
            message += f'  ... и ещё {pending_count - 5} задач\n'

        message += streak_warning
        message += (
            f'\nТвой текущий уровень: {user.level} ⭐ | Серия: {user.streak} 🔥\n\n'
            f'Не теряй темп! Открой TaskMaster и отметь выполненные задачи.\n\n'
            f'— Команда TaskMaster'
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            sent_count += 1
            logger.info(f'Reminder sent to {user.email}')
        except Exception as e:
            logger.error(f'Failed to send reminder to {user.email}: {e}')

    logger.info(f'Reminders sent: {sent_count}')
    return {'sent': sent_count}
