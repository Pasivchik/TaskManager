from django.db import models


class ShopItem(models.Model):
    ITEM_TYPES = [
        ('avatar', 'Аватар'),
        ('theme', 'Тема интерфейса'),
        ('shield', 'Щит серии'),
        ('pet_accessory', 'Аксессуар питомца'),
        ('pet_color', 'Расцветка питомца'),
    ]

    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, verbose_name='Тип')
    price = models.PositiveIntegerField(verbose_name='Цена (монеты)')
    image = models.ImageField(upload_to='shop/', null=True, blank=True, verbose_name='Изображение')

    # Для тем — CSS класс который будет добавлен на body
    css_class = models.CharField(max_length=50, blank=True, verbose_name='CSS класс темы')

    # Доступен сразу или нужно покупать
    is_default = models.BooleanField(default=False, verbose_name='Доступен по умолчанию')
    is_active = models.BooleanField(default=True, verbose_name='Активен в магазине')

    class Meta:
        verbose_name = 'Товар магазина'
        verbose_name_plural = 'Товары магазина'
        ordering = ['item_type', 'price']

    def __str__(self):
        return f'{self.get_item_type_display()} — {self.name}'


class UserInventory(models.Model):
    """Купленные пользователем предметы."""
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='inventory',
        verbose_name='Пользователь'
    )
    item = models.ForeignKey(
        ShopItem,
        on_delete=models.CASCADE,
        related_name='owners',
        verbose_name='Предмет'
    )
    purchased_at = models.DateTimeField(auto_now_add=True, verbose_name='Куплено')

    class Meta:
        verbose_name = 'Инвентарь пользователя'
        verbose_name_plural = 'Инвентарь пользователей'
        unique_together = ('user', 'item')

    def __str__(self):
        return f'{self.user.username} — {self.item.name}'
