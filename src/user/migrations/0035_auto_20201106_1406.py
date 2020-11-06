# Generated by Django 2.2 on 2020-11-06 14:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0034_termsandconditionacceptance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='termsandconditionacceptance',
            name='profile_type',
            field=models.CharField(max_length=255, verbose_name='Profile Type'),
        ),
        migrations.AlterField(
            model_name='termsandconditionacceptance',
            name='user_agent',
            field=models.TextField(max_length=1000, verbose_name='User Agent'),
        ),
    ]
