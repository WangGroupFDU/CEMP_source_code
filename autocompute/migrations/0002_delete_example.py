

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('autocompute', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Example',
        ),
    ]
