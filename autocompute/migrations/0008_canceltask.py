

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('autocompute', '0007_completedtask_queuedtask_runningtask'),
    ]

    operations = [
        migrations.CreateModel(
            name='CancelTask',
            fields=[
            ],
            options={
                'verbose_name': 'Cancel Task',
                'verbose_name_plural': 'Cancel Tasks',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('autocompute.computetask',),
        ),
    ]
