import calendar
import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.conf import settings


class Category(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name='Пользователь'
    )
    name = models.CharField(max_length=50, verbose_name='Название')
    color = models.CharField(max_length=7, default='#6c757d', verbose_name='Цвет (HEX)')
    icon = models.CharField(max_length=30, default='📁', verbose_name='Иконка (эмодзи)')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name


class Task(models.Model):
    REPEATING_TASK_TYPES = ('daily', 'recurring')
    OVERDUE_REWARD_PERCENT = 50

    TASK_TYPES = [
        ('daily', 'Ежедневная'),
        ('once', 'Разовая'),
        ('recurring', 'Повторяющаяся'),
        ('goal', 'Долгосрочная цель'),
    ]

    PRIORITIES = [
        (1, 'Низкий'),
        (2, 'Средний'),
        (3, 'Высокий'),
    ]

    DIFFICULTIES = [
        (1, 'Лёгкая'),
        (2, 'Средняя'),
        (3, 'Сложная'),
        (4, 'Очень сложная'),
    ]

    # XP и монеты за каждый уровень сложности
    XP_REWARD = {1: 10, 2: 25, 3: 50, 4: 100}
    COIN_REWARD = {1: 5, 2: 10, 3: 20, 4: 40}

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Пользователь'
    )
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    task_type = models.CharField(max_length=20, choices=TASK_TYPES, default='once', verbose_name='Тип')
    priority = models.IntegerField(choices=PRIORITIES, default=2, verbose_name='Приоритет')
    difficulty = models.IntegerField(choices=DIFFICULTIES, default=2, verbose_name='Сложность')
    category = models.ForeignKey(
        Category,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='tasks',
        verbose_name='Категория'
    )
    due_date = models.DateField(null=True, blank=True, verbose_name='Дата выполнения')
    is_completed = models.BooleanField(default=False, verbose_name='Выполнена')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Завершена в')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создана')
    repeat_group = models.UUIDField(
        null=True, blank=True, db_index=True,
        verbose_name='Группа повтора'
    )
    repeat_interval_days = models.PositiveIntegerField(default=1, verbose_name='Интервал повтора в днях')
    repeat_stopped = models.BooleanField(default=False, verbose_name='Повтор остановлен')

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['-priority', 'due_date', 'created_at']

    def __str__(self):
        return self.title

    def is_repeating_task(self):
        return self.task_type in self.REPEATING_TASK_TYPES

    def normalize_repeat_fields(self):
        changed = []

        if self.is_repeating_task():
            if not self.repeat_group:
                self.repeat_group = uuid.uuid4()
                changed.append('repeat_group')

            interval = self.repeat_interval_days or 1
            if self.task_type == 'daily':
                interval = 1
            elif self.task_type == 'recurring':
                interval = max(2, interval)
            if self.repeat_interval_days != interval:
                self.repeat_interval_days = interval
                changed.append('repeat_interval_days')
        else:
            if self.repeat_group is not None:
                self.repeat_group = None
                changed.append('repeat_group')
            if self.repeat_interval_days != 1:
                self.repeat_interval_days = 1
                changed.append('repeat_interval_days')
            if self.repeat_stopped:
                self.repeat_stopped = False
                changed.append('repeat_stopped')

        return changed

    def save(self, *args, **kwargs):
        changed = self.normalize_repeat_fields()
        update_fields = kwargs.get('update_fields')

        if update_fields is not None and changed:
            kwargs['update_fields'] = list(set(update_fields) | set(changed))

        super().save(*args, **kwargs)

    def get_base_xp_reward(self):
        return self.XP_REWARD.get(self.difficulty, 25)

    def get_base_coin_reward(self):
        return self.COIN_REWARD.get(self.difficulty, 10)

    def get_reward_percent(self):
        return self.OVERDUE_REWARD_PERCENT if self.is_overdue() else 100

    def apply_reward_percent(self, amount):
        percent = self.get_reward_percent()
        return max(1, (amount * percent + 99) // 100)

    def get_xp_reward(self):
        return self.apply_reward_percent(self.get_base_xp_reward())

    def get_coin_reward(self):
        return self.apply_reward_percent(self.get_base_coin_reward())

    @staticmethod
    def add_months(source_date, months=1):
        month = source_date.month - 1 + months
        year = source_date.year + month // 12
        month = month % 12 + 1
        day = min(source_date.day, calendar.monthrange(year, month)[1])
        return source_date.replace(year=year, month=month, day=day)

    def next_repeat_date(self, from_date=None):
        base_date = from_date or self.due_date or timezone.localdate()

        if self.task_type == 'daily':
            return base_date + timedelta(days=1)
        if self.task_type == 'recurring':
            return base_date + timedelta(days=max(2, self.repeat_interval_days or 2))
        return None

    def repeat_label(self):
        if self.task_type == 'daily':
            return 'каждый день'
        if self.task_type == 'recurring':
            return f'каждые {max(2, self.repeat_interval_days or 2)} дн.'
        return ''

    def create_repeat_occurrence(self, due_date):
        if not self.is_repeating_task() or self.repeat_stopped or not due_date:
            return None

        if not self.repeat_group:
            self.save()

        group_is_stopped = Task.objects.filter(
            user=self.user,
            repeat_group=self.repeat_group,
            repeat_stopped=True,
        ).exists()
        if group_is_stopped:
            return None

        exists = Task.objects.filter(
            user=self.user,
            repeat_group=self.repeat_group,
            due_date=due_date,
        ).exists()
        if exists:
            return None

        return Task.objects.create(
            user=self.user,
            title=self.title,
            description=self.description,
            task_type=self.task_type,
            priority=self.priority,
            difficulty=self.difficulty,
            category=self.category,
            due_date=due_date,
            repeat_group=self.repeat_group,
            repeat_interval_days=self.repeat_interval_days,
        )

    def create_next_repeat_occurrence(self):
        next_date = self.next_repeat_date()
        return self.create_repeat_occurrence(next_date)

    def complete(self):
        """Отметить задачу выполненной и начислить награды."""
        if self.is_completed:
            return False

        xp = self.get_xp_reward()
        coins = self.get_coin_reward()
        reward_percent = self.get_reward_percent()

        self.is_completed = True
        self.completed_at = timezone.now()
        self.save(update_fields=['is_completed', 'completed_at'])
        next_task = self.create_next_repeat_occurrence()

        user = self.user

        leveled_up = user.add_xp(xp)
        user.add_coins(coins)
        user.update_streak()

        # Проверяем достижения
        from apps.gamification.services import check_achievements
        check_achievements(user)

        return {
            'xp': xp,
            'coins': coins,
            'reward_percent': reward_percent,
            'leveled_up': leveled_up,
            'next_task_created': bool(next_task),
            'next_task_due_date': next_task.due_date if next_task else None,
        }

    def priority_label(self):
        return dict(self.PRIORITIES).get(self.priority, '')

    def difficulty_label(self):
        return dict(self.DIFFICULTIES).get(self.difficulty, '')

    def is_overdue(self):
        if self.due_date and not self.is_completed:
            return self.due_date < timezone.now().date()
        return False
