

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crystals', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Crystal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=20)),
                ('chemsys', models.CharField(max_length=20)),
                ('density', models.DecimalField(decimal_places=4, max_digits=20)),
                ('density_atomic', models.DecimalField(decimal_places=4, max_digits=20)),
                ('deprecated', models.CharField(max_length=20)),
                ('energy_per_atom', models.DecimalField(decimal_places=4, max_digits=20)),
                ('es_source_calc_id', models.CharField(max_length=20)),
                ('formula_anonymous', models.CharField(max_length=20)),
                ('is_gap_direct', models.CharField(max_length=20)),
                ('is_magnetic', models.CharField(max_length=20)),
                ('is_metal', models.CharField(max_length=20)),
                ('is_stable', models.CharField(max_length=20)),
                ('nelements', models.SmallIntegerField()),
                ('nsites', models.SmallIntegerField()),
                ('num_magnetic_sites', models.SmallIntegerField()),
                ('num_unique_magnetic_sites', models.SmallIntegerField()),
                ('ordering', models.CharField(max_length=20)),
                ('theoretical', models.CharField(max_length=20)),
                ('total_magnetization', models.DecimalField(decimal_places=4, max_digits=20)),
                ('volume', models.DecimalField(decimal_places=4, max_digits=20)),
            ],
        ),
        migrations.DeleteModel(
            name='Crystal_Li',
        ),
    ]
