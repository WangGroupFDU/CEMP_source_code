

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polymer', '0004_alter_experiment_polymer_data_bandgap_ev_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment_polymer_data',
            name='Reference',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
