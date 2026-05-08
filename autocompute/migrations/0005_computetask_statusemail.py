

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("autocompute", "0004_computetask_pid"),
    ]

    operations = [
        migrations.AddField(
            model_name="computetask",
            name="statusemail",
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
