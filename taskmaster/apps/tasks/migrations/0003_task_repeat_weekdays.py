from django.db import migrations, models


def fill_repeat_weekdays(apps, schema_editor):
    Task = apps.get_model('tasks', 'Task')
    for task in Task.objects.filter(task_type__in=['daily', 'recurring']):
        if task.task_type == 'daily':
            task.repeat_weekdays = '0,1,2,3,4,5,6'
        elif task.due_date:
            task.repeat_weekdays = str(task.due_date.weekday())
        else:
            task.repeat_weekdays = '0'
        task.save(update_fields=['repeat_weekdays'])


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_task_repeat_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='repeat_weekdays',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Дни недели повтора'),
        ),
        migrations.RunPython(fill_repeat_weekdays, migrations.RunPython.noop),
    ]
