

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polymer', '0006_calculated_monomer_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calculated_monomer_data',
            name='Monomer_Type',
            field=models.CharField(max_length=255),
        ),
    ]
