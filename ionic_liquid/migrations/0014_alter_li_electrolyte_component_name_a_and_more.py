

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ionic_liquid", "0013_electrolyte_li_electrolyte"),
    ]

    operations = [
        migrations.AlterField(
            model_name="li_electrolyte",
            name="Component_Name_A",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="li_electrolyte",
            name="Component_Name_B",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="li_electrolyte",
            name="Component_SMILES_A",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="li_electrolyte",
            name="Component_SMILES_B",
            field=models.CharField(max_length=255),
        ),
    ]
