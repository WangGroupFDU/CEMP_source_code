

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polymer', '0007_alter_calculated_monomer_data_monomer_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='calculated_polymer_data',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(max_length=255)),
                ('reactant_1', models.CharField(max_length=255)),
                ('reactant_2', models.CharField(max_length=255)),
                ('psmiles', models.CharField(max_length=255)),
                ('SMILES', models.CharField(max_length=255)),
                ('Energy_Hatree', models.FloatField(blank=True, null=True)),
                ('es', models.FloatField(blank=True, null=True)),
                ('reaction_type', models.FloatField(blank=True, null=True)),
                ('Isotropic_Polarizability_au', models.FloatField(blank=True, null=True)),
                ('HOMO_eV', models.FloatField(blank=True, null=True)),
                ('LUMO_eV', models.FloatField(blank=True, null=True)),
                ('Inner_energy_correction_Hatree', models.FloatField(blank=True, null=True)),
                ('Thermal_correction_to_Enthalpy_Hatree', models.FloatField(blank=True, null=True)),
                ('Thermal_correction_to_Gibbs_Free_Energy_Hatree', models.FloatField(blank=True, null=True)),
                ('Entropy_Hatree', models.FloatField(blank=True, null=True)),
                ('Dipole_Debye', models.FloatField(blank=True, null=True)),
                ('Gibbs_Free_Energy_Hatree', models.FloatField(blank=True, null=True)),
                ('Enthalpy_Hatree', models.FloatField(blank=True, null=True)),
                ('HOMO_LUMO_Gap_eV', models.FloatField(blank=True, null=True)),
            ],
        ),
    ]
