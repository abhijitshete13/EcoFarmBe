# Generated by Django 2.2 on 2020-07-03 07:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0036_profilereport_report_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profilereport',
            name='vendor_profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profile_report', to='vendor.VendorProfile', verbose_name='VendorProfile'),
        ),
    ]
