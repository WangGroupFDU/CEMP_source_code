

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ionic_liquid", "0016_ilgenerator_il_ilscore"),
    ]

    operations = [
        migrations.DeleteModel(
            name="ILgenerator_IL",
        ),
    ]
