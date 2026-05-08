

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Crystal_Li',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=20)),
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
        migrations.CreateModel(
            name='Crystal_properties',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=200)),
                ('formula', models.CharField(max_length=200)),
                ('cation', models.CharField(max_length=200)),
                ('anion', models.CharField(max_length=200)),
                ('cation_type', models.CharField(max_length=200)),
                ('anion_type', models.CharField(max_length=200)),
                ('ECW', models.FloatField(default=None)),
                ('melting_point', models.CharField(default=None, max_length=200)),
                ('conductivity', models.FloatField(default=None)),
                ('viscosity', models.CharField(default=None, max_length=200)),
                ('density', models.FloatField(default=None)),
                ('T_conductivity', models.IntegerField(default=None)),
                ('T_viscosity', models.IntegerField(default=None)),
                ('T_density', models.IntegerField(default=None)),
                ('conductivity_norm', models.FloatField(default=None)),
                ('viscosity_norm', models.FloatField(default=None)),
                ('density_norm', models.FloatField(default=None)),
            ],
        ),
        migrations.CreateModel(
            name='Crystal_smiles_psi4',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('smile_form', models.CharField(max_length=200)),
                ('energy', models.FloatField()),
                ('HOMO', models.FloatField()),
                ('LUMO', models.FloatField()),
                ('dipole_x', models.FloatField()),
                ('dipole_y', models.FloatField()),
                ('dipole_z', models.FloatField()),
                ('dipole_total', models.FloatField()),
                ('type', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Crystal_smiles_rdkit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('smile_form', models.CharField(max_length=200)),
                ('Asphericity', models.FloatField()),
                ('Eccentricity', models.FloatField()),
                ('NPR1', models.FloatField()),
                ('NPR2', models.FloatField()),
                ('PMI1', models.FloatField()),
                ('PMI2', models.FloatField()),
                ('PMI3', models.FloatField()),
                ('RadiusOfGyration', models.FloatField()),
                ('SpherocityIndex', models.FloatField()),
                ('ExactMolWt', models.FloatField()),
                ('FpDensityMorgan1', models.FloatField()),
                ('FpDensityMorgan2', models.FloatField()),
                ('HeavyAtomMolWt', models.FloatField()),
                ('MaxAbsPartialCharge', models.FloatField()),
                ('MaxPartialCharge', models.FloatField()),
                ('MinPartialCharge', models.FloatField()),
                ('NumRadicalElectrons', models.FloatField()),
                ('NumValenceElectrons', models.FloatField()),
                ('volume', models.FloatField()),
                ('type', models.CharField(max_length=200)),
            ],
        ),
    ]
