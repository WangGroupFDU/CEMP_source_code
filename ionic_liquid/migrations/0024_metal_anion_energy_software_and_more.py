

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ionic_liquid', '0023_alter_il_ml_data_anion_smiles_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='metal_anion_energy',
            name='Software',
            field=models.CharField(default='Gaussian', help_text='Calculation Software', max_length=255),
        ),
        migrations.AddField(
            model_name='metal_anion_energy',
            name='Theory_Level',
            field=models.CharField(default='opt+freq: b3lyp/6-311G** em=gd3bj\nenergy: M062X/6-311G+(2d, p) em=gd3', help_text='Calcualtion Theory Level', max_length=255),
        ),
    ]
