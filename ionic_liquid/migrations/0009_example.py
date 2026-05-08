

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ionic_liquid', '0008_metal_anion_energy'),
    ]

    operations = [
        migrations.CreateModel(
            name='Example',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('X1', models.CharField(max_length=255)),
                ('X2', models.CharField(max_length=255)),
                ('X3', models.CharField(max_length=255)),
                ('X4', models.CharField(max_length=255)),
            ],
        ),
    ]
