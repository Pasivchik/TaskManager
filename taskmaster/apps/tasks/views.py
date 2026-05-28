import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages

from .models import Task, Category
from .forms import TaskForm, CategoryForm
from .services import generate_due_repeated_tasks


class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        today = timezone.now().date()
        generate_due_repeated_tasks(user=user, through_date=today)

        # Задачи на сегодня. Долгосрочные цели видны каждый день до дедлайна.
        today_tasks = Task.objects.filter(
            user=user,
            is_completed=False
        ).filter(
            Q(due_date=today) |
            Q(task_type='goal', due_date__gte=today)
        ).select_related('category').order_by('-priority', 'due_date')

        overdue_tasks = Task.objects.filter(
            user=user,
            due_date__lt=today,
            is_completed=False,
        ).select_related('category').order_by('due_date', '-priority')

        # Задачи без даты (висящие)
        pending_tasks = Task.objects.filter(
            user=user,
            due_date__isnull=True,
            is_completed=False
        ).select_related('category').order_by('-priority')[:5]

        # Завершённые сегодня
        completed_today = Task.objects.filter(
            user=user,
            completed_at__date=today
        ).count()

        # Всего задач на сегодня (для прогресс-бара)
        total_today = today_tasks.count() + completed_today
        progress_percent = int((completed_today / total_today * 100)) if total_today > 0 else 0

        context = {
            'today_tasks': today_tasks,
            'pending_tasks': pending_tasks,
            'overdue_tasks': overdue_tasks,
            'completed_today': completed_today,
            'total_today': total_today,
            'progress_percent': progress_percent,
            'today': today,
            'form': TaskForm(user=user),
        }
        return render(request, 'tasks/dashboard.html', context)


class TaskListView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        generate_due_repeated_tasks(user=user)

        status = request.GET.get('status', 'active')
        task_type = request.GET.get('type', '')
        category_id = request.GET.get('category', '')

        tasks = Task.objects.filter(user=user).select_related('category')

        if status == 'active':
            tasks = tasks.filter(is_completed=False)
        elif status == 'completed':
            tasks = tasks.filter(is_completed=True)

        if task_type:
            tasks = tasks.filter(task_type=task_type)

        if category_id:
            tasks = tasks.filter(category_id=category_id)

        categories = Category.objects.filter(user=user)
        form = TaskForm(user=user)

        context = {
            'tasks': tasks,
            'categories': categories,
            'form': form,
            'status': status,
            'task_type': task_type,
        }
        return render(request, 'tasks/task_list.html', context)


class TaskCreateView(LoginRequiredMixin, View):
    def post(self, request):
        form = TaskForm(user=request.user, data=request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, f'Задача "{task.title}" создана! 📝')
        else:
            for error in form.errors.values():
                messages.error(request, error.as_text())

        next_url = request.POST.get('next', '/')
        return redirect(next_url)


class TaskUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        form = TaskForm(user=request.user, instance=task)
        return render(request, 'tasks/task_edit.html', {'form': form, 'task': task})

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        form = TaskForm(user=request.user, data=request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Задача обновлена ✅')
            return redirect('tasks:list')
        return render(request, 'tasks/task_edit.html', {'form': form, 'task': task})


class TaskDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        task.delete()
        messages.success(request, 'Задача удалена 🗑️')
        return redirect(request.POST.get('next', 'tasks:list'))


class TaskCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        result = task.complete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if result:
                request.user.refresh_from_db()
                return JsonResponse({
                    'status': 'ok',
                    'xp': result['xp'],
                    'coins': result['coins'],
                    'reward_percent': result['reward_percent'],
                    'leveled_up': result['leveled_up'],
                    'new_level': request.user.level,
                    'new_xp': request.user.xp,
                    'new_coins': request.user.coins,
                    'new_streak': request.user.streak,
                    'xp_percent': request.user.xp_progress_percent(),
                    'xp_needed': request.user.xp_for_next_level(),
                    'next_task_created': result['next_task_created'],
                    'next_task_due_date': (
                        result['next_task_due_date'].isoformat()
                        if result['next_task_due_date'] else None
                    ),
                })
            return JsonResponse({'status': 'already_done'})

        if result:
            msg = f'Задача выполнена! +{result["xp"]} XP, +{result["coins"]} монет 🎉'
            if result['reward_percent'] < 100:
                msg += f' Награда снижена до {result["reward_percent"]}% из-за просрочки.'
            if result['leveled_up']:
                msg += f' Новый уровень: {request.user.level}! 🆙'
            if result['next_task_created'] and result['next_task_due_date']:
                msg += f' Следующая копия создана на {result["next_task_due_date"].strftime("%d.%m.%Y")}.'
            messages.success(request, msg)
        return redirect(request.POST.get('next', '/'))


class TaskStopRepeatView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)

        if not task.is_repeating_task():
            messages.warning(request, 'У этой задачи нет повтора.')
            return redirect(request.POST.get('next', 'tasks:list'))

        if not task.repeat_group:
            task.save()

        Task.objects.filter(
            user=request.user,
            repeat_group=task.repeat_group,
        ).update(repeat_stopped=True)

        removed_future = Task.objects.filter(
            user=request.user,
            repeat_group=task.repeat_group,
            is_completed=False,
            due_date__gt=timezone.localdate(),
        ).exclude(pk=task.pk).delete()[0]

        msg = 'Повтор задачи остановлен. Новые копии больше не будут создаваться.'
        if removed_future:
            msg += f' Будущие копии удалены: {removed_future}.'
        messages.success(request, msg)
        return redirect(request.POST.get('next', 'tasks:list'))


# ── Категории ────────────────────────────────────────────────────

@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(data=request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.user = request.user
            cat.icon = '📁'
            name = cat.name
            if Category.objects.filter(user=request.user, name=name).exists():
                messages.error(request, f'Категория «{name}» уже существует.')
            else:
                cat.save()
                messages.success(request, f'Категория «{name}» создана!')
    return redirect(request.POST.get('next', 'tasks:list'))


@login_required
def category_update(request, pk):
    cat = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(data=request.POST, instance=cat)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.user = request.user
            updated.icon = cat.icon or '📁'
            name = updated.name
            duplicate = Category.objects.filter(
                user=request.user,
                name=name,
            ).exclude(pk=cat.pk).exists()
            if duplicate:
                messages.error(request, f'Категория «{name}» уже существует.')
            else:
                updated.save()
                messages.success(request, f'Категория «{name}» обновлена.')
        else:
            for error in form.errors.values():
                messages.error(request, error.as_text())
    return redirect(request.POST.get('next', 'tasks:list'))


@login_required
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        cat.delete()
        messages.success(request, 'Категория удалена.')
    return redirect('tasks:list')
