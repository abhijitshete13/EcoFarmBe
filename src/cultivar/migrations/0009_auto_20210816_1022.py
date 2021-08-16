# Generated by Django 2.2 on 2021-08-16 10:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cultivar', '0008_auto_20210816_1018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cultivar',
            name='cultivar_type',
            field=models.CharField(blank=True, choices=[('Sativa', 'Sativa'), ('Indica', 'Indica'), ('Hybrid', 'Hybrid')], max_length=50, null=True, verbose_name='Cultivar Type'),
        ),
    ]
