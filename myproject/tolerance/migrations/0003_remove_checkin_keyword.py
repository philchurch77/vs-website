from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tolerance', '0002_weeklymap_observation'),
    ]

    operations = [
        migrations.DeleteModel(
            name='DailyCheckIn',
        ),
        migrations.DeleteModel(
            name='Keyword',
        ),
    ]
