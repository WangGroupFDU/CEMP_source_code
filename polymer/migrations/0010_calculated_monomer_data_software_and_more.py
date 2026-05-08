

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polymer', '0009_alter_calculated_polymer_data_reaction_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='calculated_monomer_data',
            name='Software',
            field=models.CharField(default='ORCA', help_text='Calculation Software', max_length=255),
        ),
        migrations.AddField(
            model_name='calculated_monomer_data',
            name='Source',
            field=models.CharField(default='QC', help_text='From Quantum Chemistry Calculation', max_length=255),
        ),
        migrations.AddField(
            model_name='calculated_monomer_data',
            name='Theory_Level',
            field=models.CharField(default='opt+freq: b3lyp/def2-TZVP em=gd3bj\nenergy: wB97M-V/ma-def2-TZVP', help_text='Calcualtion Theory Level', max_length=255),
        ),
        migrations.AddField(
            model_name='calculated_polymer_data',
            name='Software',
            field=models.CharField(default='ORCA', help_text='Calculation Software', max_length=255),
        ),
        migrations.AddField(
            model_name='calculated_polymer_data',
            name='Source',
            field=models.CharField(default='QC', help_text='From Quantum Chemistry Calculation', max_length=255),
        ),
        migrations.AddField(
            model_name='calculated_polymer_data',
            name='Theory_Level',
            field=models.CharField(default='opt+freq: b3lyp/def2-TZVP em=gd3bj\nenergy: wB97M-V/ma-def2-TZVP', help_text='Calcualtion Theory Level', max_length=255),
        ),
    ]
