

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("autocompute", "0013_computetask_server_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="computetask",
            name="status_message",
            field=models.TextField(
                blank=True,
                help_text="补充记录任务状态变化原因，例如超期清理、人工终止等。",
                null=True,
            ),
        ),
    ]
