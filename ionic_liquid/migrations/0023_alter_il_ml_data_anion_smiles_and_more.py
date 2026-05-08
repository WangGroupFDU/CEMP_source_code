

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ionic_liquid', '0022_alter_il_ml_data_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='il_ml_data',
            name='Anion_SMILES',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='il_ml_data',
            name='Anion_SMILES_type',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='il_ml_data',
            name='Cation_SMILES',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='il_ml_data',
            name='Cation_SMILES_type',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='il_ml_data',
            name='Conductivity_mS_per_cm',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='il_ml_data',
            name='ECW_V',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='il_ml_data',
            name='Name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='il_ml_data',
            name='SMILES',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='il_ml_data',
            name='Tm_K',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='il_ml_data',
            name='Type',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='il_tm_conductivity_ecw_data',
            name='Anion_SMILES',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='il_tm_conductivity_ecw_data',
            name='Anion_SMILES_type',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='il_tm_conductivity_ecw_data',
            name='Cation_SMILES',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='il_tm_conductivity_ecw_data',
            name='Cation_SMILES_type',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='il_tm_conductivity_ecw_data',
            name='Conductivity_mS_per_cm',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='il_tm_conductivity_ecw_data',
            name='ECW_V',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='il_tm_conductivity_ecw_data',
            name='Name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='il_tm_conductivity_ecw_data',
            name='SMILES',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='il_tm_conductivity_ecw_data',
            name='Tm_K',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='il_tm_conductivity_ecw_data',
            name='Type',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
