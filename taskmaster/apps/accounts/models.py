from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Расширенная модель пользователя с полями геймификации."""

    # Геймификация
    level = models.PositiveIntegerField(default=1, verbose_name='Уровень')
    xp = models.PositiveIntegerField(default=0, verbose_name='Опыт (XP)')
    coins = models.PositiveIntegerField(default=0, verbose_name='Монеты')
    streak = models.PositiveIntegerField(default=0, verbose_name='Текущая серия')
    max_streak = models.PositiveIntegerField(default=0, verbose_name='Лучшая серия')
    last_activity_date = models.DateField(null=True, blank=True, verbose_name='Последняя активность')

    # Щит серии (количество активных щитов)
    streak_shields = models.PositiveIntegerField(default=0, verbose_name='Щиты серии')

    # Профиль
    theme = models.ForeignKey(
        'shop.ShopItem',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='theme_users',
        limit_choices_to={'item_type': 'theme'},
        verbose_name='Тема интерфейса'
    )
    pet_accessory = models.ForeignKey(
        'shop.ShopItem',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='pet_accessory_users',
        limit_choices_to={'item_type': 'pet_accessory'},
        verbose_name='Аксессуар питомца'
    )
    pet_color = models.ForeignKey(
        'shop.ShopItem',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='pet_color_users',
        limit_choices_to={'item_type': 'pet_color'},
        verbose_name='Расцветка питомца'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username

    # ── XP и уровни ──────────────────────────────────────────────

    def xp_for_next_level(self):
        """Сколько XP нужно для следующего уровня."""
        return int(100 * (self.level ** 1.5))

    def xp_progress_percent(self):
        """Прогресс до следующего уровня в процентах."""
        needed = self.xp_for_next_level()
        if needed == 0:
            return 100
        return min(int((self.xp / needed) * 100), 100)

    def add_xp(self, amount: int):
        """Начислить XP и повысить уровень если нужно."""
        self.xp += amount
        leveled_up = False
        while self.xp >= self.xp_for_next_level():
            self.xp -= self.xp_for_next_level()
            self.level += 1
            leveled_up = True
        self.save(update_fields=['xp', 'level'])
        return leveled_up

    def add_coins(self, amount: int):
        """Начислить монеты."""
        self.coins += amount
        self.save(update_fields=['coins'])

    def spend_coins(self, amount: int) -> bool:
        """Потратить монеты. Возвращает False если недостаточно."""
        if self.coins < amount:
            return False
        self.coins -= amount
        self.save(update_fields=['coins'])
        return True

    # ── Streak ───────────────────────────────────────────────────

    def update_streak(self):
        """Обновить серию при выполнении задачи."""
        today = timezone.now().date()
        yesterday = today - timezone.timedelta(days=1)

        if self.last_activity_date == today:
            return  # Уже обновляли сегодня

        if self.last_activity_date == yesterday or self.last_activity_date is None:
            self.streak += 1
        else:
            # Пропустили дни — сброс
            self.streak = 1

        self.last_activity_date = today
        if self.streak > self.max_streak:
            self.max_streak = self.streak

        self.save(update_fields=['streak', 'max_streak', 'last_activity_date'])

    def get_theme_css(self):
        """CSS-класс темы."""
        if self.theme:
            return self.theme.css_class
        return 'theme-dark'

    def get_pet_accessory_css(self):
        """CSS-класс выбранного аксессуара питомца."""
        if self.pet_accessory:
            return self.pet_accessory.css_class
        return ''

    def get_pet_color_css(self):
        """CSS-класс выбранной расцветки питомца."""
        if self.pet_color:
            return self.pet_color.css_class
        return ''

    def is_pet_sad_after_reset(self):
        """Питомец грустит один день после сброса серии."""
        if self.streak != 0 or not self.last_activity_date:
            return False
        reset_day = self.last_activity_date + timezone.timedelta(days=2)
        return reset_day == timezone.now().date()

    def get_pet_state(self):
        """Настроение питомца зависит от текущей серии."""
        if self.is_pet_sad_after_reset():
            return 'sad'
        if self.streak >= 7:
            return 'happy'
        if self.streak >= 3:
            return 'neutral'
        return 'sleepy'
