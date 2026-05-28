from .models import Achievement, UserAchievement


def check_achievements(user):
    """
    Проверить все достижения для пользователя и выдать незаработанные.
    Вызывается после каждого выполнения задачи.
    """
    new_achievements = []

    # Rewards from one achievement can unlock another achievement, so keep
    # checking until a pass unlocks nothing new.
    while True:
        already_unlocked = set(
            UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
        )
        all_achievements = Achievement.objects.exclude(id__in=already_unlocked)

        user.refresh_from_db()
        tasks_completed = user.tasks.filter(is_completed=True).count()
        total_coins = user.coins

        unlocked_this_pass = []

        for achievement in all_achievements:
            unlocked = False

            if achievement.condition_type in ('tasks_completed', 'tasks_total'):
                unlocked = tasks_completed >= achievement.condition_value

            elif achievement.condition_type == 'streak_days':
                unlocked = user.streak >= achievement.condition_value

            elif achievement.condition_type == 'level_reached':
                unlocked = user.level >= achievement.condition_value

            elif achievement.condition_type == 'coins_earned':
                unlocked = total_coins >= achievement.condition_value

            if unlocked:
                ua, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement,
                )
                if not created:
                    continue

                unlocked_this_pass.append(ua)

                # Выдаём награду за достижение
                if achievement.xp_reward:
                    user.add_xp(achievement.xp_reward)
                if achievement.coin_reward:
                    user.add_coins(achievement.coin_reward)

        if not unlocked_this_pass:
            break

        new_achievements.extend(unlocked_this_pass)

    return new_achievements
