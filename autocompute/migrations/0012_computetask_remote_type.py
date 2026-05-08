

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autocompute', '0011_computetask_core_hours_computetask_scope_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='computetask',
            name='remote_type',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
