

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0006_userprofile_daily_task_limit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='auto_compute_permission',
            field=models.BooleanField(default=False),
        ),
    ]
