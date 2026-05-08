

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polymer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Polyelectrolyte',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('polyelectrolyte', models.CharField(max_length=255)),
                ('copolymer', models.CharField(max_length=255)),
                ('cation', models.CharField(max_length=255)),
                ('anion', models.CharField(max_length=255)),
                ('repeat_unit', models.CharField(max_length=255)),
                ('dielectric_constant', models.CharField(max_length=255)),
                ('chemical_structure', models.CharField(max_length=255)),
                ('hydrophilic_hydrophobic', models.CharField(max_length=255)),
                ('functional_group', models.CharField(max_length=255)),
                ('application_function', models.CharField(max_length=255)),
                ('reference', models.CharField(max_length=255)),
                ('synonyms', models.CharField(max_length=255)),
                ('chemdraw_file', models.CharField(max_length=255)),
            ],
        ),
    ]
