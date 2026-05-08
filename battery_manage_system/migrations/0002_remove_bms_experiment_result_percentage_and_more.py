

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("battery_manage_system", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="bms_experiment_result",
            name="percentage",
        ),
        migrations.AddField(
            model_name="bms_experiment_result",
            name="polymer_percentage",
            field=models.PositiveSmallIntegerField(
                default=15, verbose_name="聚合物在固态电解质中百分比"
            ),
        ),
        migrations.AlterField(
            model_name="bms_experiment_result",
            name="bms_rawfile",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="battery_manage_system/",
                validators=[
                    django.core.validators.FileExtensionValidator(["csv", "txt"])
                ],
                verbose_name="BMS实验源文件",
            ),
        ),
    ]
