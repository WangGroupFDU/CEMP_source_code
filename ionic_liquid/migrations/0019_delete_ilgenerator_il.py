

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ionic_liquid", "0018_ilgenerator_il"),
    ]

    operations = [
        migrations.DeleteModel(
            name="ILgenerator_IL",
        ),
    ]
