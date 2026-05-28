from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'level', 'xp', 'coins', 'streak', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'level')
    fieldsets = UserAdmin.fieldsets + (
        ('Геймификация', {
            'fields': ('level', 'xp', 'coins', 'streak', 'max_streak',
                       'streak_shields', 'last_activity_date', 'theme',
                       'pet_accessory', 'pet_color')
        }),
    )
