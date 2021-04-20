# Generated by Django 2.2 on 2021-04-20 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bill', '0004_auto_20210420_0854'),
    ]

    operations = [
        migrations.AddField(
            model_name='estimate',
            name='db_status',
            field=models.CharField(choices=[('draft', 'draft'), ('sent', 'sent'), ('signed', 'signed')], default='draft', max_length=50, verbose_name='Progress'),
        ),
        migrations.AlterField(
            model_name='estimate',
            name='organization',
            field=models.CharField(choices=[('EFD', 'efd'), ('EFL', 'efl'), ('EFN', 'efn')], default='efd', max_length=50, verbose_name='Organization'),
        ),
    ]
