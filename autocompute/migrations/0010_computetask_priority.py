

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autocompute', '0009_delete_canceltask_taskmonitor'),
    ]

    operations = [
        migrations.AddField(
            model_name='computetask',
            name='priority',
            field=models.PositiveSmallIntegerField(default=3),
        ),
    ]
