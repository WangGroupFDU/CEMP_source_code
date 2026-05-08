

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BMS_experiment_result",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "cathode",
                    models.CharField(default="", max_length=10, verbose_name="阳极"),
                ),
                (
                    "anode",
                    models.CharField(default="Li", max_length=10, verbose_name="阴极"),
                ),
                (
                    "polymer",
                    models.CharField(default="PBDT", max_length=10, verbose_name="聚合物"),
                ),
                (
                    "ionic_liquid",
                    models.CharField(default="", max_length=15, verbose_name="离子液体"),
                ),
                ("intristic_viscosity", models.PositiveSmallIntegerField(default=5)),
                ("percentage", models.PositiveSmallIntegerField(default=15)),
                (
                    "ionic_liquid_electrolyte",
                    models.CharField(default="", max_length=25, verbose_name="阴极"),
                ),
                (
                    "li_conc",
                    models.DecimalField(decimal_places=2, default=1.6, max_digits=5),
                ),
                ("temperature", models.IntegerField(default=25)),
                (
                    "pressure",
                    models.DecimalField(decimal_places=2, default=0.7, max_digits=5),
                ),
                ("thickness", models.PositiveIntegerField(default=100)),
                (
                    "bms_rawfile",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="battery_manage_system",
                        validators=[
                            django.core.validators.FileExtensionValidator(
                                ["csv", "txt"]
                            )
                        ],
                        verbose_name="BMS实验源文件",
                    ),
                ),
            ],
        ),
    ]
