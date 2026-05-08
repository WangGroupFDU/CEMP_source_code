

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("register", "0002_captcha"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="calculating_authority",
            field=models.BooleanField(default=True),
        ),
    ]
