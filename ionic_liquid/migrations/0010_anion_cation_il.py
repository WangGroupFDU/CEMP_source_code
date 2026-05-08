

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ionic_liquid", "0009_example"),
    ]

    operations = [
        migrations.CreateModel(
            name="Anion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("Name", models.CharField(max_length=255)),
                ("SMILES", models.CharField(max_length=255)),
                ("Energy_Hatree", models.FloatField()),
                ("Thermal_correction_to_Gibbs_Free_Energy_Hatree", models.FloatField()),
                ("Thermal_correction_to_Enthalpy_Hatree", models.FloatField()),
                ("Entropy_J_per_mol_K", models.FloatField()),
                ("HOMO_Hatree", models.FloatField()),
                ("LUMO_Hatree", models.FloatField()),
                ("Dipole_Debye", models.FloatField()),
                ("Gibbs_Free_Energy_Hatree", models.FloatField()),
                ("Enthalpy_Hatree", models.FloatField()),
                ("ECW_V", models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name="Cation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("Name", models.CharField(max_length=255)),
                ("SMILES", models.CharField(max_length=255)),
                ("Energy_Hatree", models.FloatField()),
                ("Thermal_correction_to_Gibbs_Free_Energy_Hatree", models.FloatField()),
                ("Thermal_correction_to_Enthalpy_Hatree", models.FloatField()),
                ("Entropy_J_per_mol_K", models.FloatField()),
                ("HOMO_Hatree", models.FloatField()),
                ("LUMO_Hatree", models.FloatField()),
                ("Dipole_Debye", models.FloatField()),
                ("Gibbs_Free_Energy_Hatree", models.FloatField()),
                ("Enthalpy_Hatree", models.FloatField()),
                ("ECW_V", models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name="IL",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("Name", models.CharField(max_length=255)),
                ("SMILES", models.CharField(max_length=255)),
                ("Energy_Hatree", models.FloatField()),
                ("Thermal_correction_to_Gibbs_Free_Energy_Hatree", models.FloatField()),
                ("Thermal_correction_to_Enthalpy_Hatree", models.FloatField()),
                ("Entropy_J_per_mol_K", models.FloatField()),
                ("HOMO_Hatree", models.FloatField()),
                ("LUMO_Hatree", models.FloatField()),
                ("Dipole_Debye", models.FloatField()),
                ("Gibbs_Free_Energy_Hatree", models.FloatField()),
                ("Enthalpy_Hatree", models.FloatField()),
                ("ECW_V", models.FloatField()),
            ],
        ),
    ]
