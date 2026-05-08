

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autocompute', '0010_computetask_priority'),
    ]

    operations = [
        migrations.AddField(
            model_name='computetask',
            name='core_hours',
            field=models.FloatField(blank=True, help_text='任务消耗的总核心小时数（CPU hours）', null=True),
        ),
        migrations.AddField(
            model_name='computetask',
            name='scope_name',
            field=models.CharField(blank=True, help_text='任务所属 cgroup.scope 名称（如 CEMPjobs.slice）', max_length=200, null=True),
        ),
    ]
