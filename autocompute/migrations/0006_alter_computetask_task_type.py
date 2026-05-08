

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("autocompute", "0005_computetask_statusemail"),
    ]

    operations = [
        migrations.AlterField(
            model_name="computetask",
            name="task_type",
            field=models.CharField(
                blank=True, default="default_type", max_length=255, null=True
            ),
        ),
    ]
