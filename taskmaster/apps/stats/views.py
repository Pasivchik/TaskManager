import json
from datetime import timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate

from apps.tasks.models import Task


class StatsView(LoginRequiredMixin, TemplateView):
    template_name = 'stats/stats.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=29)

        # ── Активность за последние 30 дней ──────────────────────
        activity_qs = (
            Task.objects.filter(
                user=user,
                is_completed=True,
                completed_at__date__gte=thirty_days_ago,
            )
            .annotate(day=TruncDate('completed_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )

        overdue_qs = (
            Task.objects.filter(
                user=user,
                is_completed=False,
                due_date__gte=thirty_days_ago,
                due_date__lt=today,
            )
            .values('due_date')
            .annotate(count=Count('id'))
            .order_by('due_date')
        )

        # Заполняем пропущенные дни нулями
        activity_map = {item['day']: item['count'] for item in activity_qs}
        overdue_map = {item['due_date']: item['count'] for item in overdue_qs}
        activity_labels = []
        activity_data = []
        overdue_activity_data = []
        for i in range(30):
            day = thirty_days_ago + timedelta(days=i)
            activity_labels.append(day.strftime('%d.%m'))
            activity_data.append(activity_map.get(day, 0))
            overdue_activity_data.append(overdue_map.get(day, 0))

        # ── По категориям ─────────────────────────────────────────
        by_category = (
            Task.objects.filter(user=user, is_completed=True)
            .values('category__name', 'category__color')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        cat_labels = []
        cat_data = []
        cat_colors = []
        for item in by_category:
            cat_labels.append(item['category__name'] or 'Без категории')
            cat_data.append(item['count'])
            cat_colors.append(item['category__color'] or '#6c757d')

        # ── По типу задач ─────────────────────────────────────────
        by_type = (
            Task.objects.filter(user=user, is_completed=True)
            .values('task_type')
            .annotate(count=Count('id'))
        )
        type_map = {item['task_type']: item['count'] for item in by_type}

        # ── Общая статистика ──────────────────────────────────────
        total_tasks = Task.objects.filter(user=user).count()
        completed_tasks = Task.objects.filter(user=user, is_completed=True).count()
        completion_rate = int(completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Среднее задач в день (за последние 30 дней)
        avg_per_day = round(sum(activity_data) / 30, 1)

        ctx.update({
            'activity_labels': json.dumps(activity_labels),
            'activity_data': json.dumps(activity_data),
            'overdue_activity_data': json.dumps(overdue_activity_data),
            'cat_labels': json.dumps(cat_labels),
            'cat_data': json.dumps(cat_data),
            'cat_colors': json.dumps(cat_colors),
            'type_map': type_map,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': completion_rate,
            'avg_per_day': avg_per_day,
            'max_streak': user.max_streak,
            'current_streak': user.streak,
            'level': user.level,
            'xp': user.xp,
        })
        return ctx
