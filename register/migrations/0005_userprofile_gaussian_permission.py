

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0004_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='gaussian_permission',
            field=models.BooleanField(default=False),
        ),
    ]
