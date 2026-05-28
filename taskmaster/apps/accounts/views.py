from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages

from .forms import RegisterForm, LoginForm
from .models import User


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('dashboard')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f'Добро пожаловать, {user.username}! Твоё приключение начинается 🎮')
        return redirect(self.success_url)


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


@login_required
def profile_view(request):
    user = request.user
    from apps.gamification.models import UserAchievement
    from apps.shop.models import ShopItem, UserInventory
    achievements = UserAchievement.objects.filter(user=user).select_related('achievement').order_by('-date_unlocked')

    # Инвентарь: купленные + базовые предметы
    owned = list(user.inventory.select_related('item').all())
    owned_item_ids = {inv.item_id for inv in owned}
    default_items = ShopItem.objects.filter(is_default=True).exclude(item_type='avatar')

    context = {
        'achievements': achievements,
        'tasks_completed': user.tasks.filter(is_completed=True).count(),
        'inventory_items': owned,
        'default_items': default_items,
        'owned_item_ids': owned_item_ids,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')
