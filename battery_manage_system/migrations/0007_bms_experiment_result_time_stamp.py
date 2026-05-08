

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('battery_manage_system', '0006_alter_bms_experiment_result_remark'),
    ]

    operations = [
        migrations.AddField(
            model_name='bms_experiment_result',
            name='time_stamp',
            field=models.CharField(default='a timestamp', max_length=255, null=True),
        ),
    ]
