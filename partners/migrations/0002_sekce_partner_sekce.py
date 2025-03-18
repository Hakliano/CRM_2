from django.db import migrations, models

def create_default_sekce(apps, schema_editor):
    Sekce = apps.get_model('partners', 'Sekce')
    Sekce.objects.get_or_create(id=1, nazev='Vlasy')

class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sekce',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nazev', models.CharField(max_length=100)),
            ],
        ),
        migrations.RunPython(create_default_sekce),
        migrations.AddField(
            model_name='partner',
            name='sekce',
            field=models.ForeignKey(default=1, on_delete=models.SET_DEFAULT, to='partners.sekce'),
        ),
    ]
