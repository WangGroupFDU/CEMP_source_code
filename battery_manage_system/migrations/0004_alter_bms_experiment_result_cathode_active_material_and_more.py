

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('battery_manage_system', '0003_bms_experiment_result_cathode_active_material_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bms_experiment_result',
            name='cathode_active_material',
            field=models.PositiveSmallIntegerField(default=11, verbose_name='阳极活性物质载量'),
        ),
        migrations.AlterField(
            model_name='bms_experiment_result',
            name='li_metal_thickness',
            field=models.PositiveSmallIntegerField(default=180, verbose_name='锂金属厚度'),
        ),
    ]
