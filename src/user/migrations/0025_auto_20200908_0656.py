# Generated by Django 2.2 on 2020-09-08 06:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0024_user_membership_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='status',
            field=models.CharField(choices=[('not_started', 'Not Started'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('approved', 'Approved'), ('crop_overview', 'Crop Overview'), ('financial_overview', 'Financial Overview'), ('done', 'Done')], default='not_started', max_length=20),
        ),
    ]
