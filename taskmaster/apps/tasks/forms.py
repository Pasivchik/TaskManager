from django import forms
from django.utils import timezone

from .models import Task, Category


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'task_type', 'priority', 'difficulty',
            'category', 'due_date', 'repeat_interval_days',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название задачи'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Описание (необязательно)'}),
            'task_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'repeat_interval_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2,
                'step': 1,
                'placeholder': 'Например: 3',
            }),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user)
        self.fields['category'].empty_label = 'Без категории'
        self.fields['category'].required = False
        self.fields['repeat_interval_days'].required = False
        self.fields['repeat_interval_days'].initial = 2
        self.fields['repeat_interval_days'].label = 'Период повтора, дней'
        self.fields['repeat_interval_days'].help_text = (
            'Используется только для типа "Повторяющаяся". '
            'Для ежедневной и долгосрочной задачи поле не используется.'
        )

    def clean(self):
        cleaned = super().clean()
        task_type = cleaned.get('task_type')
        repeat_interval_days = cleaned.get('repeat_interval_days')

        if task_type in Task.REPEATING_TASK_TYPES and not cleaned.get('due_date'):
            cleaned['due_date'] = timezone.localdate()

        if task_type == 'recurring':
            if not repeat_interval_days:
                self.add_error('repeat_interval_days', 'Укажите частоту повтора в днях.')
            elif repeat_interval_days < 2:
                self.add_error('repeat_interval_days', 'Повторяющаяся задача должна повторяться раз в 2 дня или реже.')
        elif task_type == 'daily':
            cleaned['repeat_interval_days'] = 1
        elif task_type == 'goal':
            cleaned['repeat_interval_days'] = 1
        else:
            cleaned['repeat_interval_days'] = 1

        return cleaned


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название категории', 'required': True}),
            'color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
        }

    def save(self, commit=True):
        category = super().save(commit=False)
        category.icon = category.icon or '📁'
        if commit:
            category.save()
        return category
