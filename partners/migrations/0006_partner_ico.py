# Generated by Django 4.2 on 2025-03-18 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0005_alter_partner_latitude_alter_partner_longitude'),
    ]

    operations = [
        migrations.AddField(
            model_name='partner',
            name='ICO',
            field=models.CharField(max_length=8, null=True, unique=True),
        ),
    ]
