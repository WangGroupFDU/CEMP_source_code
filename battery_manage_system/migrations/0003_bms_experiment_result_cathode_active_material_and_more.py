

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('battery_manage_system', '0002_remove_bms_experiment_result_percentage_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bms_experiment_result',
            name='cathode_active_material',
            field=models.IntegerField(default='11', max_length=4, verbose_name='阳极活性物质载量'),
        ),
        migrations.AddField(
            model_name='bms_experiment_result',
            name='charge_rate',
            field=models.CharField(default='0.5C', max_length=10, verbose_name='charge_rate'),
        ),
        migrations.AddField(
            model_name='bms_experiment_result',
            name='li_metal_thickness',
            field=models.IntegerField(default='180', max_length=4, verbose_name='锂金属厚度'),
        ),
        migrations.AddField(
            model_name='bms_experiment_result',
            name='magnetic_field_direction',
            field=models.CharField(default='No', max_length=15, verbose_name='磁场方向'),
        ),
        migrations.AddField(
            model_name='bms_experiment_result',
            name='remark',
            field=models.CharField(default=' ', max_length=15, verbose_name='Remarks'),
        ),
        migrations.AlterField(
            model_name='bms_experiment_result',
            name='bms_rawfile',
            field=models.FileField(blank=True, null=True, upload_to='battery_manage_system/', validators=[django.core.validators.FileExtensionValidator(['csv', 'txt', 'xlsx'])], verbose_name='BMS实验源文件'),
        ),
        migrations.AlterField(
            model_name='bms_experiment_result',
            name='cathode',
            field=models.CharField(default='LFP', max_length=10, verbose_name='阳极'),
        ),
        migrations.AlterField(
            model_name='bms_experiment_result',
            name='intristic_viscosity',
            field=models.PositiveSmallIntegerField(default=15),
        ),
        migrations.AlterField(
            model_name='bms_experiment_result',
            name='ionic_liquid_electrolyte',
            field=models.CharField(default='', max_length=25, verbose_name='离子液体电解质'),
        ),
        migrations.AlterField(
            model_name='bms_experiment_result',
            name='thickness',
            field=models.PositiveIntegerField(default=100, verbose_name='膜的厚度'),
        ),
    ]
