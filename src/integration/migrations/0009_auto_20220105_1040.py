# Generated by Django 2.2 on 2022-01-05 10:40

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('brand', '0113_auto_20211222_0707'),
        ('integration', '0008_auto_20211111_0725'),
    ]

    operations = [
        migrations.CreateModel(
            name='BoxSignDocType',
            fields=[
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(choices=[('agreement', 'Agreement'), ('w9', 'W9')], max_length=100, primary_key=True, serialize=False, unique=True, verbose_name='Name')),
                ('display_name', models.CharField(max_length=100, verbose_name='Display Name')),
                ('need_approval', models.BooleanField(default=False, verbose_name='Need Approval')),
            ],
            options={
                'verbose_name': 'Box Sign Doc Type',
                'verbose_name_plural': 'Box Sign Doc Type',
            },
        ),
        migrations.CreateModel(
            name='BoxSignFinalCopyReader',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('email', models.EmailField(max_length=255, verbose_name='Email')),
                ('doc_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='final_copy_readers', to='integration.BoxSignDocType', verbose_name='Doc Type')),
            ],
            options={
                'verbose_name': 'Box Sign Final Copy Reader',
                'verbose_name_plural': 'Box Sign Final Copy Readers',
            },
        ),
        migrations.CreateModel(
            name='BoxSignDocApprover',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255, verbose_name='Approver Name')),
                ('email', models.EmailField(max_length=255, verbose_name='Approver Email')),
                ('prefill_data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, verbose_name='Approver prefill Data')),
                ('doc_type', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='approver', to='integration.BoxSignDocType', verbose_name='Doc Type')),
            ],
            options={
                'verbose_name': 'Box Sign Doc Approver',
                'verbose_name_plural': 'Box Sign Doc Approvers',
            },
        ),
        migrations.CreateModel(
            name='BoxSign',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('request_id', models.CharField(max_length=255, unique=True, verbose_name='Request ID')),
                ('status', models.CharField(blank=True, max_length=255, null=True, verbose_name='Status')),
                ('signer_decision', models.CharField(blank=True, max_length=255, null=True, verbose_name='Signer Decision')),
                ('output_file_id', models.CharField(max_length=255, verbose_name='Action ID')),
                ('fields', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True)),
                ('response', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True)),
                ('doc_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='box_sign_requests', to='integration.BoxSignDocType', verbose_name='License')),
                ('license', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='box_sign_requests', to='brand.License', verbose_name='License')),
            ],
            options={
                'verbose_name': 'Box Sign Request',
                'verbose_name_plural': 'Box Sign Requests',
                'unique_together': {('license', 'request_id')},
            },
        ),
    ]
