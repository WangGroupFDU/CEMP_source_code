

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('battery_manage_system', '0004_alter_bms_experiment_result_cathode_active_material_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bms_experiment_result',
            name='bms_rawfile',
            field=models.FileField(default='No_files', upload_to='battery_manage_system/', validators=[django.core.validators.FileExtensionValidator(['csv', 'txt', 'xlsx'])], verbose_name='BMS实验源文件'),
            preserve_default=False,
        ),
    ]
