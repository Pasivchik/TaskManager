from django.db import models
from django.conf import settings


class Achievement(models.Model):
    """Определение достижения."""

    CONDITION_TYPES = [
        ('tasks_completed', 'Всего выполнено задач'),
        ('tasks_total', 'Всего выполнено задач'),
        ('streak_days', 'Серия дней'),
        ('level_reached', 'Достигнут уровень'),
        ('coins_earned', 'Монет заработано всего'),
    ]

    title = models.CharField(max_length=100, verbose_name='Название')
    description = models.CharField(max_length=255, verbose_name='Описание')
    icon = models.CharField(max_length=10, default='🏆', verbose_name='Иконка (эмодзи)')
    condition_type = models.CharField(max_length=30, choices=CONDITION_TYPES, verbose_name='Тип условия')
    condition_value = models.PositiveIntegerField(verbose_name='Значение условия')

    # Награда за получение достижения
    xp_reward = models.PositiveIntegerField(default=0, verbose_name='Награда XP')
    coin_reward = models.PositiveIntegerField(default=0, verbose_name='Награда монеты')

    class Meta:
        verbose_name = 'Достижение'
        verbose_name_plural = 'Достижения'
        ordering = ['condition_type', 'condition_value']

    def __str__(self):
        return f'{self.icon} {self.title}'


class UserAchievement(models.Model):
    """Полученное пользователем достижение."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='achievements',
        verbose_name='Пользователь'
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='user_achievements',
        verbose_name='Достижение'
    )
    date_unlocked = models.DateTimeField(auto_now_add=True, verbose_name='Получено')

    class Meta:
        verbose_name = 'Достижение пользователя'
        verbose_name_plural = 'Достижения пользователей'
        unique_together = ('user', 'achievement')

    def __str__(self):
        return f'{self.user.username} — {self.achievement.title}'
