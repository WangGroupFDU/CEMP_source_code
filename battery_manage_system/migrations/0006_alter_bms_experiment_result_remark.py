

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('battery_manage_system', '0005_alter_bms_experiment_result_bms_rawfile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bms_experiment_result',
            name='remark',
            field=models.CharField(blank=True, default='default', max_length=15, null=True, verbose_name='Remarks'),
        ),
    ]
