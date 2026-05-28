"""
Команда для заполнения БД начальными данными:
- Достижения
- Товары магазина (2 темы, 2 аватара, щит)

Запуск: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from apps.gamification.models import Achievement
from apps.shop.models import ShopItem


class Command(BaseCommand):
    help = 'Заполнить БД начальными данными (достижения, магазин)'

    def handle(self, *args, **options):
        self._create_achievements()
        self._create_shop_items()
        self.stdout.write(self.style.SUCCESS('✅ Данные успешно загружены!'))

    def _create_achievements(self):
        achievements = [
            # Задачи
            dict(title='Первые шаги', description='Выполни первую задачу', icon='👶',
                 condition_type='tasks_completed', condition_value=1,
                 xp_reward=50, coin_reward=20),
            dict(title='Десятка', description='Выполни 10 задач', icon='🔟',
                 condition_type='tasks_completed', condition_value=10,
                 xp_reward=100, coin_reward=50),
            dict(title='Продуктивный', description='Выполни 50 задач', icon='💪',
                 condition_type='tasks_completed', condition_value=50,
                 xp_reward=300, coin_reward=150),
            dict(title='Машина задач', description='Выполни 100 задач', icon='🤖',
                 condition_type='tasks_completed', condition_value=100,
                 xp_reward=500, coin_reward=300),
            dict(title='Легенда', description='Выполни 500 задач', icon='🏅',
                 condition_type='tasks_completed', condition_value=500,
                 xp_reward=2000, coin_reward=1000),
            # Серии
            dict(title='Три дня подряд', description='Поддерживай серию 3 дня', icon='🔥',
                 condition_type='streak_days', condition_value=3,
                 xp_reward=75, coin_reward=30),
            dict(title='Неделя!', description='Серия 7 дней', icon='🗓️',
                 condition_type='streak_days', condition_value=7,
                 xp_reward=150, coin_reward=75),
            dict(title='Месяц без остановки', description='Серия 30 дней', icon='💫',
                 condition_type='streak_days', condition_value=30,
                 xp_reward=1000, coin_reward=500),
            dict(title='Стальная воля', description='Серия 100 дней', icon='⚡',
                 condition_type='streak_days', condition_value=100,
                 xp_reward=5000, coin_reward=2000),
            # Уровни
            dict(title='Новичок', description='Достигни 5 уровня', icon='🌱',
                 condition_type='level_reached', condition_value=5,
                 xp_reward=0, coin_reward=100),
            dict(title='Опытный', description='Достигни 10 уровня', icon='🌿',
                 condition_type='level_reached', condition_value=10,
                 xp_reward=0, coin_reward=300),
            dict(title='Мастер', description='Достигни 25 уровня', icon='🌳',
                 condition_type='level_reached', condition_value=25,
                 xp_reward=0, coin_reward=1000),
        ]

        created = 0
        for data in achievements:
            _, was_created = Achievement.objects.get_or_create(
                title=data['title'],
                defaults=data
            )
            if was_created:
                created += 1

        self.stdout.write(f'  Достижений создано: {created}')

    def _create_shop_items(self):
        items = [
            # Аватары (is_default=True — доступен сразу)
            dict(name='Стандартный аватар', description='Базовый аватар игрока',
                 item_type='avatar', price=0, is_default=True, css_class=''),
            dict(name='Золотой герой', description='Блестящий аватар для настоящих чемпионов',
                 item_type='avatar', price=200, is_default=False, css_class=''),
            # Темы
            dict(name='Стандартная тема', description='Тёмно-фиолетовая тема по умолчанию',
                 item_type='theme', price=0, is_default=True, css_class='theme-default'),
            dict(name='Закат', description='Тёплые оранжевые тона заката',
                 item_type='theme', price=150, is_default=False, css_class='theme-sunset'),
            dict(name='Лесная тень', description='Спокойные зелёные тона природы',
                 item_type='theme', price=150, is_default=False, css_class='theme-forest'),
            # Щит серии
            dict(name='Щит серии', description='Защищает твою серию от сброса на 1 день',
                 item_type='shield', price=100, is_default=False, css_class=''),
        ]

        created = 0
        for data in items:
            _, was_created = ShopItem.objects.get_or_create(
                name=data['name'],
                item_type=data['item_type'],
                defaults=data
            )
            if was_created:
                created += 1

        self.stdout.write(f'  Товаров магазина создано: {created}')
