# Generated by Django 2.2 on 2021-11-26 07:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0107_auto_20211126_0710'),
    ]

    operations = [
        migrations.AlterField(
            model_name='license',
            name='license_status',
            field=models.CharField(choices=[('Active', 'Active'), ('Expired', 'Expired')], default='Active', max_length=100, verbose_name='License Status'),
        ),
    ]
