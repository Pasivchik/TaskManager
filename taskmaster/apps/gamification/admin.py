from django.contrib import admin
from .models import Achievement, UserAchievement


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('icon', 'title', 'condition_type', 'condition_value', 'xp_reward', 'coin_reward')
    list_filter = ('condition_type',)
    search_fields = ('title',)


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'date_unlocked')
    list_filter = ('achievement',)
    raw_id_fields = ('user',)
