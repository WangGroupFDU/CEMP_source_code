

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crystals', '0002_crystal_delete_crystal_li'),
    ]

    operations = [
        migrations.CreateModel(
            name='Crystals',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('crystal', models.CharField(default='X', max_length=25)),
                ('label', models.CharField(max_length=25)),
                ('band_gap', models.DecimalField(decimal_places=3, default=0, max_digits=25)),
                ('chemsys', models.CharField(max_length=25)),
                ('density', models.DecimalField(decimal_places=3, max_digits=25)),
                ('density_atomic', models.DecimalField(decimal_places=3, max_digits=25)),
                ('deprecated', models.CharField(max_length=25)),
                ('energy_above_hull', models.DecimalField(decimal_places=5, max_digits=25)),
                ('energy_per_atom', models.DecimalField(decimal_places=3, max_digits=25)),
                ('formation_energy_per_atom', models.DecimalField(decimal_places=5, max_digits=25)),
                ('formula_anonymous', models.CharField(max_length=25)),
                ('formula_pretty', models.CharField(max_length=25)),
                ('is_gap_direct', models.CharField(max_length=25)),
                ('is_magnetic', models.CharField(max_length=25)),
                ('is_metal', models.CharField(max_length=25)),
                ('is_stable', models.CharField(max_length=25)),
                ('nelements', models.SmallIntegerField()),
                ('nsites', models.SmallIntegerField()),
                ('num_magnetic_sites', models.SmallIntegerField()),
                ('num_unique_magnetic_sites', models.SmallIntegerField()),
                ('ordering', models.CharField(max_length=25)),
                ('theoretical', models.CharField(max_length=25)),
                ('total_magnetization', models.DecimalField(decimal_places=3, max_digits=25)),
                ('volume', models.DecimalField(decimal_places=3, max_digits=25)),
            ],
        ),
        migrations.DeleteModel(
            name='Crystal',
        ),
    ]
