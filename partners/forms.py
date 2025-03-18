from django import forms
from .models import Sekce, Partner
from django.contrib.auth.models import User

class PartnerForm(forms.ModelForm):
    class Meta:
        model = Partner
        fields = '__all__'
        exclude = ['created_by', 'kontaktovan', 'vysledek_kontaktu']

class PartnerFilterForm(forms.Form):
    jmeno = forms.CharField(required=False, label="Jméno")
    mesto = forms.CharField(required=False, label="Město")
    cast_obce = forms.CharField(required=False, label="Část obce")
    sekce = forms.ModelChoiceField(
        queryset=Sekce.objects.all(),
        required=False,
        label="Sekce",
        empty_label="--- Vyberte sekci ---"
    )
    oslovovaci_poradi = forms.IntegerField(required=False, label="Oslovovací pořadí")
    created_by = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label="Vytvořil uživatel",
        empty_label="--- Vyberte uživatele ---"
    )
    kontaktovan = forms.ChoiceField(
        choices=[('', '--- Nerozhoduje ---'), ('True', 'Ano'), ('False', 'Ne')],
        required=False,
        label="Kontaktován"
    )
    vysledek_kontaktu = forms.CharField(required=False, label="Výsledek kontaktu")
