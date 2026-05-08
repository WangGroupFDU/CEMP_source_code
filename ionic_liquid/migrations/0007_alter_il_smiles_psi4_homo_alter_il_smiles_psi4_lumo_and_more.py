

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ionic_liquid', '0006_alter_il_properties_ecw_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='il_smiles_psi4',
            name='HOMO',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='il_smiles_psi4',
            name='LUMO',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='il_smiles_psi4',
            name='dipole_total',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='il_smiles_psi4',
            name='dipole_x',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='il_smiles_psi4',
            name='dipole_y',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='il_smiles_psi4',
            name='dipole_z',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='il_smiles_psi4',
            name='energy',
            field=models.FloatField(),
        ),
    ]
