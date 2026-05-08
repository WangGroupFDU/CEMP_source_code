

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("autocompute", "0003_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="computetask",
            name="pid",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
