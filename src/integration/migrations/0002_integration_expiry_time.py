# Generated by Django 2.2 on 2020-05-15 09:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('integration', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='integration',
            name='expiry_time',
            field=models.BigIntegerField(blank=True, null=True, verbose_name='expiry_time_crm'),
        ),
    ]
