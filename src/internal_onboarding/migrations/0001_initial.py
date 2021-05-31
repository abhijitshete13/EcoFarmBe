# Generated by Django 2.2 on 2021-05-31 10:21

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('brand', '0075_license_crm_output'),
    ]

    operations = [
        migrations.CreateModel(
            name='InternalOnboardingInvite',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('user_joining_platform', 'User Joining Platform'), ('completed', 'Completed')], default='pending', max_length=60)),
                ('completed_on', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='internal_onboarding_invites_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('license', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='internal_onboarding_invites', to='brand.License', verbose_name='Licenses')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='internal_onboarding_invites', to='brand.Organization', verbose_name='Organization')),
                ('roles', models.ManyToManyField(related_name='internal_onboarding_invites', to='brand.OrganizationRole', verbose_name='Organization Roles')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='internal_onboarding_invites', to=settings.AUTH_USER_MODEL, verbose_name='Organization')),
            ],
            options={
                'verbose_name': 'Internal Onboarding Invite',
                'verbose_name_plural': 'Internal Onboarding Invites',
            },
        ),
        migrations.CreateModel(
            name='InternalOnboarding',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('license_number', models.CharField(max_length=255, verbose_name='License Number')),
                ('submitted_data', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='internal_onboardings', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
