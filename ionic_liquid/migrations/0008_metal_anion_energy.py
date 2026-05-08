

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ionic_liquid', '0007_alter_il_smiles_psi4_homo_alter_il_smiles_psi4_lumo_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='metal_anion_energy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Dimer_Name', models.CharField(max_length=255)),
                ('Dimer_SMILES', models.CharField(max_length=255)),
                ('Component_Name_A', models.CharField(max_length=255)),
                ('Component_SMILES_A', models.CharField(max_length=255)),
                ('Component_Name_B', models.CharField(max_length=255)),
                ('Component_SMILES_B', models.CharField(max_length=255)),
                ('Component_A_Energy_Hatree', models.FloatField()),
                ('Component_B_Energy_Hatree', models.FloatField()),
                ('Component_A_Thermal_correction_to_Gibbs_Free_Energy_Hatree', models.FloatField()),
                ('Component_B_Thermal_correction_to_Gibbs_Free_Energy_Hatree', models.FloatField()),
                ('Component_A_Thermal_correction_to_Enthalpy_Hatree', models.FloatField()),
                ('Component_B_Thermal_correction_to_Enthalpy_Hatree', models.FloatField()),
                ('Component_A_Entropy_J_mol_K', models.FloatField()),
                ('Component_B_Entropy_J_mol_K', models.FloatField()),
                ('Component_A_HOMO_Hatree', models.FloatField()),
                ('Component_B_HOMO_Hatree', models.FloatField()),
                ('Component_A_Dipole_Debye', models.FloatField()),
                ('Component_B_Dipole_Debye', models.FloatField()),
                ('Component_A_LUMO_Hatree', models.FloatField()),
                ('Component_B_LUMO_Hatree', models.FloatField()),
                ('Component_A_Gibbs_Free_Energy_Hatree', models.FloatField()),
                ('Component_A_Enthalpy_Hatree', models.FloatField()),
                ('Component_B_Gibbs_Free_Energy_Hatree', models.FloatField()),
                ('Component_B_Enthalpy_Hatree', models.FloatField()),
                ('Dimer_Energy_Hatree', models.FloatField()),
                ('Dimer_Thermal_correction_to_Gibbs_Free_Energy_Hatree', models.FloatField()),
                ('Dimer_Thermal_correction_to_Enthalpy_Hatree', models.FloatField()),
                ('Dimer_Entropy_J_mol_K', models.FloatField()),
                ('Dimer_HOMO_Hatree', models.FloatField()),
                ('Dimer_Dipole_Debye', models.FloatField()),
                ('Dimer_LUMO_Hatree', models.FloatField()),
                ('Dimer_Gibbs_Free_Energy_Hatree', models.FloatField()),
                ('Dimer_Enthalpy_Hatree', models.FloatField()),
                ('Binding_energy_kJ_mol', models.FloatField()),
            ],
        ),
    ]
