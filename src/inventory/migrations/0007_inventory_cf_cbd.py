# Generated by Django 2.2 on 2020-05-04 04:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0006_auto_20200429_1358'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='cf_cbd',
            field=models.FloatField(blank=True, null=True, verbose_name='Potency'),
        ),
    ]
