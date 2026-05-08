

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0005_userprofile_gaussian_permission'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='daily_task_limit',
            field=models.PositiveIntegerField(default=3, help_text='Maximum number of tasks the user can run per day (non-negative integer).', verbose_name='Daily Task Limit'),
        ),
    ]
