

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polymer', '0011_experiment_polymer_data_density'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment_polymer_data',
            name='Atomization_Energy_eV',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='experiment_polymer_data',
            name='Bandgap_Bulk_eV',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='experiment_polymer_data',
            name='Bandgap_Chain_eV',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='experiment_polymer_data',
            name='CH4_Permeability_Barrer',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='experiment_polymer_data',
            name='Crystallization_Tendency_percentage',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='experiment_polymer_data',
            name='Electron_Affinity_eV',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='experiment_polymer_data',
            name='He_Permeability_Barrer',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='experiment_polymer_data',
            name='Ionization_Energy_eV',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='experiment_polymer_data',
            name='N2_Permeability_Barrer',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
