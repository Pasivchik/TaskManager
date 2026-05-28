from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Achievement, UserAchievement


class AchievementsView(LoginRequiredMixin, ListView):
    template_name = 'gamification/achievements.html'
    context_object_name = 'all_achievements'

    def get_queryset(self):
        return Achievement.objects.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        from .services import check_achievements
        check_achievements(user)
        unlocked_ids = set(
            UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
        )
        unlocked_map = {
            ua.achievement_id: ua
            for ua in UserAchievement.objects.filter(user=user).select_related('achievement')
        }
        ctx['unlocked_ids'] = unlocked_ids
        ctx['unlocked_map'] = unlocked_map
        ctx['unlocked_count'] = len(unlocked_ids)
        ctx['total_count'] = Achievement.objects.count()
        return ctx
