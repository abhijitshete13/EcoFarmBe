# Generated by Django 2.2 on 2021-12-22 07:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0112_profilereport_selected_profiles'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profilereport',
            options={'verbose_name': 'Profile Report', 'verbose_name_plural': 'Profile Reports'},
        ),
        migrations.AlterUniqueTogether(
            name='profilereport',
            unique_together={('profile', 'name')},
        ),
    ]
