

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ionic_liquid', '0020_ilgenerator_il'),
    ]

    operations = [
        migrations.CreateModel(
            name='Anion_QC_data',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(blank=True, max_length=255, null=True)),
                ('SMILES', models.CharField(blank=True, max_length=255, null=True)),
                ('Anion_type', models.CharField(blank=True, max_length=255, null=True)),
                ('Energy_Hatree', models.FloatField(blank=True, null=True)),
                ('Thermal_correction_to_Gibbs_Free_Energy_Hatree', models.FloatField(blank=True, null=True)),
                ('Thermal_correction_to_Enthalpy_Hatree', models.FloatField(blank=True, null=True)),
                ('Entropy_J_per_mol_K', models.FloatField(blank=True, null=True)),
                ('HOMO_Hatree', models.FloatField(blank=True, null=True)),
                ('LUMO_Hatree', models.FloatField(blank=True, null=True)),
                ('Dipole_Debye', models.FloatField(blank=True, null=True)),
                ('Gibbs_Free_Energy_Hatree', models.FloatField(blank=True, null=True)),
                ('Enthalpy_Hatree', models.FloatField(blank=True, null=True)),
                ('HOMO_LUMO_Gap_eV', models.FloatField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Cation_QC_data',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(blank=True, max_length=255, null=True)),
                ('SMILES', models.CharField(blank=True, max_length=255, null=True)),
                ('Cation_type', models.CharField(blank=True, max_length=255, null=True)),
                ('Energy_Hatree', models.FloatField(blank=True, null=True)),
                ('Thermal_correction_to_Gibbs_Free_Energy_Hatree', models.FloatField(blank=True, null=True)),
                ('Thermal_correction_to_Enthalpy_Hatree', models.FloatField(blank=True, null=True)),
                ('Entropy_J_per_mol_K', models.FloatField(blank=True, null=True)),
                ('HOMO_Hatree', models.FloatField(blank=True, null=True)),
                ('LUMO_Hatree', models.FloatField(blank=True, null=True)),
                ('Dipole_Debye', models.FloatField(blank=True, null=True)),
                ('Gibbs_Free_Energy_Hatree', models.FloatField(blank=True, null=True)),
                ('Enthalpy_Hatree', models.FloatField(blank=True, null=True)),
                ('HOMO_LUMO_Gap_eV', models.FloatField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='IL_ML_data',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(max_length=255)),
                ('SMILES', models.CharField(max_length=255)),
                ('Anion_SMILES', models.CharField(max_length=255)),
                ('Cation_SMILES', models.CharField(max_length=255)),
                ('Cation_SMILES_type', models.CharField(max_length=255)),
                ('Anion_SMILES_type', models.CharField(max_length=255)),
                ('Conductivity_mS_per_cm', models.FloatField()),
                ('Tm_K', models.FloatField()),
                ('ECW_V', models.FloatField()),
                ('Type', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='IL_Tm_conductivity_ECW_data',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(max_length=255)),
                ('SMILES', models.CharField(max_length=255)),
                ('Anion_SMILES', models.CharField(max_length=255)),
                ('Cation_SMILES', models.CharField(max_length=255)),
                ('Cation_SMILES_type', models.CharField(max_length=255)),
                ('Anion_SMILES_type', models.CharField(max_length=255)),
                ('Conductivity_mS_per_cm', models.FloatField()),
                ('Tm_K', models.FloatField()),
                ('ECW_V', models.FloatField()),
                ('Type', models.FloatField()),
            ],
        ),
    ]
