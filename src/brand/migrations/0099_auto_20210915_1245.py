# Generated by Django 2.2 on 2021-09-15 12:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0098_license_business_dba'),
    ]

    operations = [
        migrations.AddField(
            model_name='license',
            name='box_folder_id',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Box Folder Id'),
        ),
        migrations.AddField(
            model_name='license',
            name='box_folder_url',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Box Folder URL'),
        ),
    ]
