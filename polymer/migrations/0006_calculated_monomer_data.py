

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polymer', '0005_experiment_polymer_data_reference'),
    ]

    operations = [
        migrations.CreateModel(
            name='calculated_monomer_data',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(max_length=255)),
                ('SMILES', models.CharField(max_length=255)),
                ('Neutral_Energy_Hatree', models.FloatField(blank=True, null=True)),
                ('Oxidation_Energy_Hatree', models.FloatField(blank=True, null=True)),
                ('Reduction_Energy_Hatree', models.FloatField(blank=True, null=True)),
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
                ('Oxidation_Potential_V', models.FloatField(blank=True, null=True)),
                ('Reduction_Potential_V', models.FloatField(blank=True, null=True)),
                ('Redox_Window_V', models.FloatField(blank=True, null=True)),
                ('Monomer_Type', models.FloatField(blank=True, null=True)),
                ('IP_Hatree', models.FloatField(blank=True, null=True)),
                ('EA_Hatree', models.FloatField(blank=True, null=True)),
                ('Mulliken_Electronegativity_Hatree', models.FloatField(blank=True, null=True)),
                ('Chemical_Potential_Hatree', models.FloatField(blank=True, null=True)),
                ('Hardness_Hatree', models.FloatField(blank=True, null=True)),
                ('Softness_Hatree', models.FloatField(blank=True, null=True)),
                ('Electrophilicity_Index_Hatree', models.FloatField(blank=True, null=True)),
                ('Corrected_Redox_Window_V', models.FloatField(blank=True, null=True)),
                ('Acetone_Gibbs_Free_Energy_Hatree', models.FloatField(blank=True, null=True)),
                ('Acetone_Solvation_Free_Energy_kJ_per_mol', models.FloatField(blank=True, null=True)),
                ('Chloroform_Gibbs_Free_Energy_Hatree', models.FloatField(blank=True, null=True)),
                ('Chloroform_Solvation_Free_Energy_kJ_per_mol', models.FloatField(blank=True, null=True)),
                ('DMF_Gibbs_Free_Energy_Hatree', models.FloatField(blank=True, null=True)),
                ('DMF_Solvation_Free_Energy_kJ_per_mol', models.FloatField(blank=True, null=True)),
                ('DMSO_Gibbs_Free_Energy_Hatree', models.FloatField(blank=True, null=True)),
                ('DMSO_Solvation_Free_Energy_kJ_per_mol', models.FloatField(blank=True, null=True)),
                ('Hexane_Gibbs_Free_Energy_Hatree', models.FloatField(blank=True, null=True)),
                ('Hexane_Solvation_Free_Energy_kJ_per_mol', models.FloatField(blank=True, null=True)),
                ('Water_Gibbs_Free_Energy_Hatree', models.FloatField(blank=True, null=True)),
                ('Water_Solvation_Free_Energy_kJ_per_mol', models.FloatField(blank=True, null=True)),
                ('THF_Gibbs_Free_Energy_Hatree', models.FloatField(blank=True, null=True)),
                ('THF_Solvation_Free_Energy_kJ_per_mol', models.FloatField(blank=True, null=True)),
            ],
        ),
    ]
