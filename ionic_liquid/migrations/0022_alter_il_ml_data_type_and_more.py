

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ionic_liquid', '0021_anion_qc_data_cation_qc_data_il_ml_data_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='il_ml_data',
            name='Type',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='il_tm_conductivity_ecw_data',
            name='Type',
            field=models.CharField(max_length=255),
        ),
    ]
