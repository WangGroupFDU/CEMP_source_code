

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polymer', '0003_experiment_polymer_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Bandgap_eV',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='CO2_Permeability_Barrer',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Compressive_Strength_MPa',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Crystallization_Temperature_K',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Dielectric_Constant_Electronic',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Dielectric_Constant_Ionic',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Dielectric_Constant_Total',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Elongation_at_Break_percentage',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Flexural_Strength_MPa',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='H2_Permeability_Barrer',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Hardness_MPa',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Impact_Strength_kJ_per_m2',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Ion_Exchange_Capacity_meq_per_g',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Limiting_Oxygen_Index_percentage',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Lower_Critical_Solution_Temperature_K',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Methanol_Permeability_cm2_per_s',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='O2_Permeability_Barrer',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Refractive_Index',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Swelling_Degree_percentage',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Td_K',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Tensile_Strength_MPa',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Tg_K',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Thermal_Conductivity_W_per_mK',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Tm_K',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Upper_Critical_Solution_Temperature_K',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Water_Contact_Angle',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Water_Uptake_percentage',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='experiment_polymer_data',
            name='Youngs_Modulus_MPa',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
