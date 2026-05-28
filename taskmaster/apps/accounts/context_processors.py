def user_profile(request):
    """Добавляет данные профиля пользователя во все шаблоны."""
    if request.user.is_authenticated:
        user = request.user
        return {
            'profile_level': user.level,
            'profile_xp': user.xp,
            'profile_xp_needed': user.xp_for_next_level(),
            'profile_xp_percent': user.xp_progress_percent(),
            'profile_coins': user.coins,
            'profile_streak': user.streak,
            'profile_theme': user.get_theme_css(),
            'profile_pet_state': user.get_pet_state(),
            'profile_pet_accessory': user.pet_accessory,
            'profile_pet_accessory_class': user.get_pet_accessory_css(),
            'profile_pet_color': user.pet_color,
            'profile_pet_color_class': user.get_pet_color_css(),
        }
    return {}
