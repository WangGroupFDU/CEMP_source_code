

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ionic_liquid', '0024_metal_anion_energy_software_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='anion',
            name='Software',
            field=models.CharField(default='Gaussian', help_text='Calculation Software', max_length=255),
        ),
        migrations.AddField(
            model_name='anion',
            name='Source',
            field=models.CharField(default='QC', help_text='From Quantum Chemistry Calculation', max_length=255),
        ),
        migrations.AddField(
            model_name='anion',
            name='Theory_Level',
            field=models.CharField(default='opt+freq: b3lyp/6-311G** em=gd3bj\nenergy: M062X/6-311G+(2d, p) em=gd3', help_text='Calcualtion Theory Level', max_length=255),
        ),
        migrations.AddField(
            model_name='anion_qc_data',
            name='Software',
            field=models.CharField(default='Gaussian', help_text='Calculation Software', max_length=255),
        ),
        migrations.AddField(
            model_name='anion_qc_data',
            name='Source',
            field=models.CharField(default='QC', help_text='From Quantum Chemistry Calculation', max_length=255),
        ),
        migrations.AddField(
            model_name='anion_qc_data',
            name='Theory_Level',
            field=models.CharField(default='opt+freq: b3lyp/6-311G** em=gd3bj\nenergy: M062X/6-311G+(2d, p) em=gd3', help_text='Calcualtion Theory Level', max_length=255),
        ),
        migrations.AddField(
            model_name='cation',
            name='Software',
            field=models.CharField(default='Gaussian', help_text='Calculation Software', max_length=255),
        ),
        migrations.AddField(
            model_name='cation',
            name='Source',
            field=models.CharField(default='QC', help_text='From Quantum Chemistry Calculation', max_length=255),
        ),
        migrations.AddField(
            model_name='cation',
            name='Theory_Level',
            field=models.CharField(default='opt+freq: b3lyp/6-311G** em=gd3bj\nenergy: M062X/6-311G+(2d, p) em=gd3', help_text='Calcualtion Theory Level', max_length=255),
        ),
        migrations.AddField(
            model_name='cation_qc_data',
            name='Software',
            field=models.CharField(default='Gaussian', help_text='Calculation Software', max_length=255),
        ),
        migrations.AddField(
            model_name='cation_qc_data',
            name='Source',
            field=models.CharField(default='QC', help_text='From Quantum Chemistry Calculation', max_length=255),
        ),
        migrations.AddField(
            model_name='cation_qc_data',
            name='Theory_Level',
            field=models.CharField(default='opt+freq: b3lyp/6-311G** em=gd3bj\nenergy: M062X/6-311G+(2d, p) em=gd3', help_text='Calcualtion Theory Level', max_length=255),
        ),
        migrations.AddField(
            model_name='electrolyte',
            name='Software',
            field=models.CharField(default='Gaussian', help_text='Calculation Software', max_length=255),
        ),
        migrations.AddField(
            model_name='electrolyte',
            name='Source',
            field=models.CharField(default='QC', help_text='From Quantum Chemistry Calculation', max_length=255),
        ),
        migrations.AddField(
            model_name='electrolyte',
            name='Theory_Level',
            field=models.CharField(default='opt+freq: b3lyp/6-311G** em=gd3bj\nenergy: M062X/6-311G+(2d, p) em=gd3', help_text='Calcualtion Theory Level', max_length=255),
        ),
        migrations.AddField(
            model_name='il',
            name='Software',
            field=models.CharField(default='Gaussian', help_text='Calculation Software', max_length=255),
        ),
        migrations.AddField(
            model_name='il',
            name='Source',
            field=models.CharField(default='QC', help_text='From Quantum Chemistry Calculation', max_length=255),
        ),
        migrations.AddField(
            model_name='il',
            name='Theory_Level',
            field=models.CharField(default='opt+freq: b3lyp/6-311G** em=gd3bj\nenergy: M062X/6-311G+(2d, p) em=gd3', help_text='Calcualtion Theory Level', max_length=255),
        ),
        migrations.AddField(
            model_name='il_ml_data',
            name='Source',
            field=models.CharField(default='ML', help_text='Predicted From ML Model', max_length=255),
        ),
        migrations.AddField(
            model_name='il_tm_conductivity_ecw_data',
            name='Source',
            field=models.CharField(default='QC and EXP', help_text='ECW From QC, Tm and Conductivity from EXP', max_length=255),
        ),
        migrations.AddField(
            model_name='li_electrolyte',
            name='Software',
            field=models.CharField(default='Gaussian', help_text='Calculation Software', max_length=255),
        ),
        migrations.AddField(
            model_name='li_electrolyte',
            name='Source',
            field=models.CharField(default='QC', help_text='From Quantum Chemistry Calculation', max_length=255),
        ),
        migrations.AddField(
            model_name='li_electrolyte',
            name='Theory_Level',
            field=models.CharField(default='opt+freq: b3lyp/6-311G** em=gd3bj\nenergy: M062X/6-311G+(2d, p) em=gd3', help_text='Calcualtion Theory Level', max_length=255),
        ),
        migrations.AddField(
            model_name='metal_anion_energy',
            name='Source',
            field=models.CharField(default='QC', help_text='From Quantum Chemistry Calculation', max_length=255),
        ),
    ]
