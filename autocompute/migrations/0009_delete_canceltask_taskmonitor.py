

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('autocompute', '0008_canceltask'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CancelTask',
        ),
        migrations.CreateModel(
            name='TaskMonitor',
            fields=[
            ],
            options={
                'verbose_name': 'Task Monitor',
                'verbose_name_plural': 'Task Monitor',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('autocompute.computetask',),
        ),
    ]
