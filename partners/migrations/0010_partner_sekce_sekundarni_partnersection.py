# Generated by Django 4.2 on 2025-04-19 00:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0009_alter_partner_latitude_alter_partner_longitude'),
    ]

    operations = [
        migrations.AddField(
            model_name='partner',
            name='sekce_sekundarni',
            field=models.ManyToManyField(blank=True, related_name='partneri_sekundarni', to='partners.sekce'),
        ),
        migrations.CreateModel(
            name='PartnerSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('partner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='partners.partner')),
                ('sekce', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='partners.sekce')),
            ],
            options={
                'unique_together': {('partner', 'sekce')},
            },
        ),
    ]
