from django import forms
from .models import Sekce, Partner
from django.contrib.auth.models import User
from decimal import Decimal, ROUND_DOWN
from django.forms.widgets import CheckboxSelectMultiple


class PartnerForm(forms.ModelForm):
    sekce_sekundarni = forms.ModelMultipleChoiceField(
        queryset=Sekce.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label="Doplňkové sekce" 
    )  
    class Meta:
        model = Partner
        fields = "__all__"
        exclude = ["created_by", "kontaktovan", "vysledek_kontaktu"]
        widgets = {
            "longitude": forms.TextInput(
                attrs={
                    "type": "text",
                    "maxlength": "40",
                    "inputmode": "decimal",
                    "placeholder": "např. 14.42076000",
                    "pattern": r"^-?\d{1,12}(\.\d{1,20})?$",
                }
            ),
            "latitude": forms.TextInput(
                attrs={
                    "type": "text",
                    "maxlength": "40",
                    "inputmode": "decimal",
                    "placeholder": "např. 50.08804000",
                    "pattern": r"^-?\d{1,12}(\.\d{1,20})?$",
                }
            ),
        }
      

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["longitude"].localize = False
        self.fields["latitude"].localize = False
        self.fields["sekce_sekundarni"].widget = forms.CheckboxSelectMultiple()
        self.fields["sekce_sekundarni"].label = "Doplňkové sekce"
        self.fields["sekce_sekundarni"].queryset = Sekce.objects.all()


    def clean_longitude(self):
        value = self.cleaned_data["longitude"]
        value = Decimal(str(value))  # konverze na Decimal
        return value.quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)


    def clean_latitude(self):
        value = self.cleaned_data["latitude"]
        value = Decimal(str(value))  # konverze na Decimal
        return value.quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)


class PartnerFilterForm(forms.Form):
    jmeno = forms.CharField(required=False, label="Jméno")
    mesto = forms.CharField(required=False, label="Město")
    cast_obce = forms.CharField(required=False, label="Část obce")
    sekce = forms.ModelChoiceField(
        queryset=Sekce.objects.all(),
        required=False,
        label="Sekce",
        empty_label="--- Vyberte sekci ---",
    )
    oslovovaci_poradi = forms.IntegerField(required=False, label="Oslovovací pořadí")
    created_by = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label="Vytvořil uživatel",
        empty_label="--- Vyberte uživatele ---",
    )
    kontaktovan = forms.ChoiceField(
        choices=[("", "--- Nerozhoduje ---"), ("True", "Ano"), ("False", "Ne")],
        required=False,
        label="Kontaktován",
    )
    vysledek_kontaktu = forms.CharField(required=False, label="Výsledek kontaktu")
