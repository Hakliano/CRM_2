# Generated by Django 4.2 on 2025-03-18 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0004_partner_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partner',
            name='latitude',
            field=models.DecimalField(decimal_places=6, default=0.0, max_digits=9),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='partner',
            name='longitude',
            field=models.DecimalField(decimal_places=6, default=0.0, max_digits=9),
            preserve_default=False,
        ),
    ]
