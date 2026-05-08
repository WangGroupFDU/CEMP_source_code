

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polymer', '0008_calculated_polymer_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calculated_polymer_data',
            name='reaction_type',
            field=models.CharField(max_length=255),
        ),
    ]
