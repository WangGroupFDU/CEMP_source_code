

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("register", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Captcha",
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
                ("code", models.CharField(max_length=10)),
                ("expire_time", models.DateTimeField()),
                ("encrypt_id", models.CharField(max_length=100)),
            ],
        ),
    ]
