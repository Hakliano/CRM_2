# Generated by Django 5.2 on 2025-05-02 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0012_partner_key_account_manager'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partner',
            name='mesto',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
