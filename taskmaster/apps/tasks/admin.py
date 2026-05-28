from django.contrib import admin
from .models import Task, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'color')
    list_filter = ('user',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'user', 'task_type', 'repeat_interval_days',
        'repeat_stopped', 'priority', 'difficulty', 'is_completed', 'due_date',
    )
    list_filter = ('task_type', 'repeat_stopped', 'priority', 'difficulty', 'is_completed')
    search_fields = ('title', 'user__username')
    raw_id_fields = ('user',)
    readonly_fields = ('repeat_group',)
