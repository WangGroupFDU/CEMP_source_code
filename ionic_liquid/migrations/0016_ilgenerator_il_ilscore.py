

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ionic_liquid", "0015_ilgenerator_il"),
    ]

    operations = [
        migrations.AddField(
            model_name="ilgenerator_il",
            name="ILScore",
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
    ]
