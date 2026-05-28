from django.utils import timezone

from .models import Task


def generate_due_repeated_tasks(user=None, through_date=None):
    """Create missed repeated task occurrences up to through_date."""
    through_date = through_date or timezone.localdate()
    base_qs = Task.objects.filter(task_type__in=Task.REPEATING_TASK_TYPES)

    if user is not None:
        base_qs = base_qs.filter(user=user)

    normalized = 0
    for task in base_qs.filter(repeat_group__isnull=True):
        task.save()
        normalized += 1

    repeat_groups = list(
        base_qs
        .exclude(repeat_group__isnull=True)
        .values_list('repeat_group', flat=True)
        .distinct()
    )

    created = 0
    for repeat_group in repeat_groups:
        group_qs = Task.objects.filter(repeat_group=repeat_group)
        if user is not None:
            group_qs = group_qs.filter(user=user)

        if group_qs.filter(repeat_stopped=True).exists():
            continue

        template = (
            group_qs
            .exclude(due_date__isnull=True)
            .order_by('-due_date', '-created_at')
            .first()
        )

        if template is None:
            template = group_qs.order_by('-created_at').first()
            if template is None:
                continue
            template.due_date = through_date
            template.save(update_fields=['due_date'])
            continue

        next_date = template.next_repeat_date(from_date=template.due_date)
        guard = 0

        while next_date and next_date <= through_date and guard < 1000:
            existing = group_qs.filter(due_date=next_date).order_by('-created_at').first()
            if existing:
                template = existing
            else:
                new_task = template.create_repeat_occurrence(next_date)
                if new_task is None:
                    break
                template = new_task
                created += 1

            next_date = template.next_repeat_date(from_date=template.due_date)
            guard += 1

    return {'created': created, 'normalized': normalized}
