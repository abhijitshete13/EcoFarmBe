# Generated by Django 2.2 on 2021-09-24 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0101_auto_20210924_1001'),
    ]

    operations = [
        migrations.AlterField(
            model_name='licenseprofile',
            name='is_account_updated_in_crm',
            field=models.BooleanField(default=False, verbose_name='Is Account Updated In CRM'),
        ),
    ]
