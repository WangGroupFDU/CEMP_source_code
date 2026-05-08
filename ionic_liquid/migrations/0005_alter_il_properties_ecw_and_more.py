

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ionic_liquid', '0004_alter_il_properties_ecw_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='il_properties',
            name='ECW',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='T_conductivity',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='T_density',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='T_viscosity',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='conductivity',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='conductivity_norm',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='density',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='density_norm',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='melting_point',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='viscosity',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='il_properties',
            name='viscosity_norm',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
    ]
