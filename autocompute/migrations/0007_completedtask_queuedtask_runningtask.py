

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('autocompute', '0006_alter_computetask_task_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompletedTask',
            fields=[
            ],
            options={
                'verbose_name': 'Completed Task',
                'verbose_name_plural': 'Completed Tasks',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('autocompute.computetask',),
        ),
        migrations.CreateModel(
            name='QueuedTask',
            fields=[
            ],
            options={
                'verbose_name': 'Queued Task',
                'verbose_name_plural': 'Queued Tasks',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('autocompute.computetask',),
        ),
        migrations.CreateModel(
            name='RunningTask',
            fields=[
            ],
            options={
                'verbose_name': 'Running Task',
                'verbose_name_plural': 'Running Tasks',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('autocompute.computetask',),
        ),
    ]
