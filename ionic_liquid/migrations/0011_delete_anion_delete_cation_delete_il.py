

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ionic_liquid', '0010_anion_cation_il'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Anion',
        ),
        migrations.DeleteModel(
            name='Cation',
        ),
        migrations.DeleteModel(
            name='IL',
        ),
    ]
