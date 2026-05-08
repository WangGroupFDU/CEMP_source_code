

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ionic_liquid", "0019_delete_ilgenerator_il"),
    ]

    operations = [
        migrations.CreateModel(
            name="ILgenerator_IL",
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
                ("Anion_Name", models.CharField(max_length=255)),
                ("Cation_Name", models.CharField(max_length=255)),
                ("Cation_SMILES_type", models.CharField(max_length=255)),
                ("Anion_SMILES", models.CharField(max_length=255)),
                ("Cation_SMILES", models.CharField(max_length=255)),
                ("conductivity", models.FloatField()),
                ("Ea", models.FloatField()),
                ("lnA", models.FloatField()),
                ("Tm", models.FloatField()),
                ("ECW", models.FloatField()),
                ("ILScore", models.FloatField()),
            ],
        ),
    ]
