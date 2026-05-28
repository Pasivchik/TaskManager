from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from .models import ShopItem, UserInventory


@method_decorator(login_required, name='dispatch')
class ShopView(ListView):
    template_name = 'shop/shop.html'
    context_object_name = 'items'

    def get_queryset(self):
        return ShopItem.objects.filter(is_active=True, is_default=False).exclude(item_type='avatar')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        owned_ids = set(
            UserInventory.objects.filter(user=user).values_list('item_id', flat=True)
        )
        # Добавляем дефолтные предметы в owned
        default_ids = set(
            ShopItem.objects.filter(is_default=True).values_list('id', flat=True)
        )
        ctx['owned_ids'] = owned_ids | default_ids
        ctx['items_by_type'] = {
            'theme': [i for i in ctx['items'] if i.item_type == 'theme'],
            'shield': [i for i in ctx['items'] if i.item_type == 'shield'],
            'pet_accessory': [i for i in ctx['items'] if i.item_type == 'pet_accessory'],
            'pet_color': [i for i in ctx['items'] if i.item_type == 'pet_color'],
        }
        return ctx


@login_required
def buy_item(request, item_id):
    if request.method != 'POST':
        return redirect('shop:shop')

    item = get_object_or_404(ShopItem, id=item_id, is_active=True)
    user = request.user

    # Проверяем что не куплено
    if UserInventory.objects.filter(user=user, item=item).exists():
        messages.warning(request, 'Этот предмет уже есть в твоём инвентаре.')
        return redirect('shop:shop')

    # Щиты — особый случай, можно покупать несколько
    if item.item_type == 'shield':
        if not user.spend_coins(item.price):
            messages.error(request, f'Недостаточно монет. Нужно {item.price} 💰')
            return redirect('shop:shop')
        user.streak_shields += 1
        user.save(update_fields=['streak_shields'])
        messages.success(request, f'Щит серии куплен! У тебя теперь {user.streak_shields} щит(а) 🛡️')
        return redirect('shop:shop')

    # Аксессуары и расцветки питомца покупаются за монеты.
    if item.item_type in ('pet_accessory', 'pet_color'):
        if not user.spend_coins(item.price):
            messages.error(request, f'Недостаточно монет. Нужно {item.price} 💰')
            return redirect('shop:shop')
        UserInventory.objects.create(user=user, item=item)
        messages.success(request, f'"{item.name}" куплен для питомца! Теперь можно применить его в профиле.')
        return redirect('shop:shop')

    # Обычная покупка
    if not user.spend_coins(item.price):
        messages.error(request, f'Недостаточно монет. Нужно {item.price} 💰')
        return redirect('shop:shop')

    UserInventory.objects.create(user=user, item=item)
    messages.success(request, f'"{item.name}" куплено! Теперь примени его в профиле.')
    return redirect('shop:shop')


@login_required
def apply_item(request, item_id):
    """Применить купленный предмет."""
    if request.method != 'POST':
        return redirect('shop:shop')

    item = get_object_or_404(ShopItem, id=item_id)
    user = request.user

    # Проверяем владение
    owns = item.is_default or UserInventory.objects.filter(user=user, item=item).exists()
    if not owns:
        messages.error(request, 'Этот предмет тебе не принадлежит.')
        return redirect('shop:shop')

    if item.item_type == 'theme':
        user.theme = item
        user.save(update_fields=['theme'])
        messages.success(request, f'Тема "{item.name}" применена! 🎨')
    elif item.item_type == 'pet_accessory':
        user.pet_accessory = item
        user.save(update_fields=['pet_accessory'])
        messages.success(request, f'Аксессуар "{item.name}" надет на питомца!')
    elif item.item_type == 'pet_color':
        user.pet_color = item
        user.save(update_fields=['pet_color'])
        messages.success(request, f'Расцветка "{item.name}" применена!')

    return redirect('accounts:profile')
