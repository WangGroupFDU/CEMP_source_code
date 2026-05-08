

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autocompute', '0012_computetask_remote_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='computetask',
            name='server_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
