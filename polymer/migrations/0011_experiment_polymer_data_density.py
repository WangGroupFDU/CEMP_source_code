

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polymer', '0010_calculated_monomer_data_software_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment_polymer_data',
            name='Density',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
