from django import forms
from django.utils import timezone

from .models import Task, Category


class TaskForm(forms.ModelForm):
    WEEKDAY_CHOICES = [
        ('0', 'Пн'),
        ('1', 'Вт'),
        ('2', 'Ср'),
        ('3', 'Чт'),
        ('4', 'Пт'),
        ('5', 'Сб'),
        ('6', 'Вс'),
    ]

    repeat_weekdays = forms.MultipleChoiceField(
        choices=WEEKDAY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'repeat-weekday-input'}),
        label='Дни недели повтора',
    )

    class Meta:
        model = Task
        fields = [
            'title', 'description', 'task_type', 'priority', 'difficulty',
            'category', 'due_date', 'repeat_weekdays',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название задачи'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Описание (необязательно)'}),
            'task_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user)
        self.fields['category'].empty_label = 'Без категории'
        self.fields['category'].required = False

        if self.instance.pk:
            self.fields['repeat_weekdays'].initial = [
                str(day) for day in self.instance.repeat_weekday_numbers()
            ]

    def clean(self):
        cleaned = super().clean()
        task_type = cleaned.get('task_type')
        repeat_weekdays = cleaned.get('repeat_weekdays') or []

        if task_type in Task.REPEATING_TASK_TYPES and not cleaned.get('due_date'):
            cleaned['due_date'] = timezone.localdate()

        if task_type == 'recurring':
            if not repeat_weekdays:
                self.add_error('repeat_weekdays', 'Выберите хотя бы один день недели.')
            else:
                cleaned['repeat_weekdays'] = Task.normalize_weekdays(repeat_weekdays)
                base_date = cleaned.get('due_date') or timezone.localdate()
                cleaned['due_date'] = Task.next_date_for_weekdays(
                    base_date,
                    cleaned['repeat_weekdays'],
                    include_start=True,
                )
        elif task_type == 'daily':
            cleaned['repeat_weekdays'] = '0,1,2,3,4,5,6'
        else:
            cleaned['repeat_weekdays'] = ''

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
