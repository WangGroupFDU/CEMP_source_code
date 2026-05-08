

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('battery_manage_system', '0007_bms_experiment_result_time_stamp'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bms_experiment_result',
            name='time_stamp',
        ),
    ]
