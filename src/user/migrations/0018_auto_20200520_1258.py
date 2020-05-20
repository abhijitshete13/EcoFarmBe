# Generated by Django 2.2 on 2020-05-20 12:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0017_auto_20200519_1121'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='profile_photo_sharable_link',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Profile Photo Sharable Link'),
        ),
        migrations.AlterField(
            model_name='user',
            name='profile_photo',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Profile Photo Box ID'),
        ),
    ]
