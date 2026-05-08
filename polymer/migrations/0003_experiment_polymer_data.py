

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polymer', '0002_polyelectrolyte'),
    ]

    operations = [
        migrations.CreateModel(
            name='experiment_polymer_data',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(max_length=255)),
                ('PSMILES', models.CharField(max_length=255)),
                ('Bandgap_eV', models.FloatField()),
                ('CO2_Permeability_Barrer', models.FloatField()),
                ('Compressive_Strength_MPa', models.FloatField()),
                ('Crystallization_Temperature_K', models.FloatField()),
                ('Elongation_at_Break_percentage', models.FloatField()),
                ('Flexural_Strength_MPa', models.FloatField()),
                ('Tg_K', models.FloatField()),
                ('H2_Permeability_Barrer', models.FloatField()),
                ('Hardness_MPa', models.FloatField()),
                ('Impact_Strength_kJ_per_m2', models.FloatField()),
                ('Ion_Exchange_Capacity_meq_per_g', models.FloatField()),
                ('Limiting_Oxygen_Index_percentage', models.FloatField()),
                ('Lower_Critical_Solution_Temperature_K', models.FloatField()),
                ('Tm_K', models.FloatField()),
                ('Methanol_Permeability_cm2_per_s', models.FloatField()),
                ('O2_Permeability_Barrer', models.FloatField()),
                ('Refractive_Index', models.FloatField()),
                ('Swelling_Degree_percentage', models.FloatField()),
                ('Thermal_Conductivity_W_per_mK', models.FloatField()),
                ('Tensile_Strength_MPa', models.FloatField()),
                ('Td_K', models.FloatField()),
                ('Upper_Critical_Solution_Temperature_K', models.FloatField()),
                ('Water_Contact_Angle', models.FloatField()),
                ('Water_Uptake_percentage', models.FloatField()),
                ('Youngs_Modulus_MPa', models.FloatField()),
                ('Dielectric_Constant_Electronic', models.FloatField()),
                ('Dielectric_Constant_Ionic', models.FloatField()),
                ('Dielectric_Constant_Total', models.FloatField()),
            ],
        ),
    ]
