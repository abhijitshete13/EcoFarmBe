# Generated by Django 2.2 on 2021-03-01 15:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0060_auto_20210223_0928'),
    ]

    operations = [
        migrations.AddField(
            model_name='custominventory',
            name='client_code',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Client Code'),
        ),
    ]
