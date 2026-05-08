

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ionic_liquid', '0005_alter_il_properties_ecw_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='il_properties',
            name='ECW',
            field=models.FloatField(default=None),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='T_conductivity',
            field=models.IntegerField(default=None),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='T_density',
            field=models.IntegerField(default=None),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='T_viscosity',
            field=models.IntegerField(default=None),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='conductivity',
            field=models.FloatField(default=None),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='conductivity_norm',
            field=models.FloatField(default=None),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='density',
            field=models.FloatField(default=None),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='density_norm',
            field=models.FloatField(default=None),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='melting_point',
            field=models.CharField(default=None, max_length=200),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='viscosity',
            field=models.CharField(default=None, max_length=200),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='viscosity_norm',
            field=models.FloatField(default=None),
        ),
    ]
