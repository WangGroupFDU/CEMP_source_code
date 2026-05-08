from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("autocompute", "0014_computetask_status_message"),
    ]

    operations = [
        migrations.AddField(
            model_name="computetask",
            name="last_heartbeat_at",
            field=models.DateTimeField(
                blank=True,
                help_text="远程任务最近一次确认仍在推进的时间戳，用于识别假活跃 pending。",
                null=True,
            ),
        ),
    ]
