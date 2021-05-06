# Generated by Django 2.2 on 2021-05-06 11:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0080_documents_mobile_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='custominventory',
            name='zoho_organization',
            field=models.CharField(choices=[('efd', 'Thrive Society (EFD LLC)'), ('efl', 'Eco Farm Labs (EFL LLC)'), ('efn', 'Eco Farm Nursery (EFN LLC)')], default='efd', max_length=100, null=True, verbose_name='Zoho Organization'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='custominventory',
            name='category_name',
            field=models.CharField(blank=True, choices=[('Wholesale - Flower', 'Wholesale - Flower'), ('In the Field', 'In the Field'), ('Flower - Tops', 'Flower - Tops'), ('Flower - Bucked Untrimmed', 'Flower - Bucked Untrimmed'), ('Flower - Bucked Untrimmed - Seeded', 'Flower - Bucked Untrimmed - Seeded'), ('Flower - Bucked Untrimmed - Contaminated', 'Flower - Bucked Untrimmed - Contaminated'), ('Flower - Small', 'Flower - Small'), ('Trim', 'Trim'), ('Packaged Goods', 'Packaged Goods'), ('Isolates', 'Isolates'), ('Isolates - CBD', 'Isolates - CBD'), ('Isolates - THC', 'Isolates - THC'), ('Isolates - CBG', 'Isolates - CBG'), ('Isolates - CBN', 'Isolates - CBN'), ('Wholesale - Concentrates', 'Wholesale - Concentrates'), ('Crude Oil', 'Crude Oil'), ('Crude Oil - THC', 'Crude Oil - THC'), ('Crude Oil - CBD', 'Crude Oil - CBD'), ('Distillate Oil', 'Distillate Oil'), ('Distillate Oil - THC', 'Distillate Oil - THC'), ('Distillate Oil - CBD', 'Distillate Oil - CBD'), ('Shatter', 'Shatter'), ('Sauce', 'Sauce'), ('Crumble', 'Crumble'), ('Kief', 'Kief'), ('Lab Testing', 'Lab Testing'), ('Terpenes', 'Terpenes'), ('Terpenes - Cultivar Specific', 'Terpenes - Cultivar Specific'), ('Terpenes - Cultivar Blended', 'Terpenes - Cultivar Blended'), ('Services', 'Services'), ('QC', 'QC'), ('Transport', 'Transport'), ('Secure Cash Handling', 'Secure Cash Handling'), ('Clones', 'Clones')], max_length=225, null=True, verbose_name='Item Category Name'),
        ),
    ]
