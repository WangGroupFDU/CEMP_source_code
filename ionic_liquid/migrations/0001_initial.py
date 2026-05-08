

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='calculate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('calculate_id', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='predict',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('predict_id', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='search',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('search_name', models.CharField(max_length=200)),
            ],
        ),
    ]
