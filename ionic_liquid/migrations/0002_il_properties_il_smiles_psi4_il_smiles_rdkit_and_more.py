

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ionic_liquid', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IL_properties',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=200)),
                ('formula', models.CharField(max_length=200)),
                ('cation', models.CharField(max_length=200)),
                ('anion', models.CharField(max_length=200)),
                ('cation_type', models.CharField(max_length=200)),
                ('anion_type', models.CharField(max_length=200)),
                ('ECW', models.DecimalField(decimal_places=1, max_digits=5)),
                ('melting_point', models.CharField(max_length=200)),
                ('conductivity', models.DecimalField(decimal_places=2, max_digits=5)),
                ('viscosity', models.CharField(max_length=200)),
                ('density', models.DecimalField(decimal_places=2, max_digits=5)),
                ('T_conductivity', models.IntegerField(default=0)),
                ('T_viscosity', models.IntegerField(default=0)),
                ('T_density', models.IntegerField(default=0)),
                ('conductivity_norm', models.DecimalField(decimal_places=2, max_digits=5)),
                ('viscosity_norm', models.DecimalField(decimal_places=2, max_digits=5)),
                ('density_norm', models.DecimalField(decimal_places=2, max_digits=5)),
            ],
        ),
        migrations.CreateModel(
            name='IL_smiles_psi4',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('smile_form', models.CharField(max_length=200)),
                ('energy', models.CharField(max_length=200)),
                ('HOMO', models.CharField(max_length=200)),
                ('LUMO', models.CharField(max_length=200)),
                ('dipole_x', models.CharField(max_length=200)),
                ('dipole_y', models.CharField(max_length=200)),
                ('dipole_z', models.CharField(max_length=200)),
                ('dipole_total', models.CharField(max_length=200)),
                ('type', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='IL_smiles_rdkit',
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
        migrations.DeleteModel(
            name='calculate',
        ),
        migrations.DeleteModel(
            name='predict',
        ),
        migrations.DeleteModel(
            name='search',
        ),
    ]
