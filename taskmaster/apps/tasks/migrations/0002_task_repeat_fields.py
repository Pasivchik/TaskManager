from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='repeat_group',
            field=models.UUIDField(blank=True, db_index=True, null=True, verbose_name='Группа повтора'),
        ),
        migrations.AddField(
            model_name='task',
            name='repeat_interval_days',
            field=models.PositiveIntegerField(default=1, verbose_name='Интервал повтора в днях'),
        ),
        migrations.AddField(
            model_name='task',
            name='repeat_stopped',
            field=models.BooleanField(default=False, verbose_name='Повтор остановлен'),
        ),
    ]
