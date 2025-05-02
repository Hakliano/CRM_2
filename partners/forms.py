from django import forms
from .models import Sekce, Partner
from django.contrib.auth.models import User
from decimal import Decimal, ROUND_DOWN
from django.forms.widgets import CheckboxSelectMultiple
from django.db.models import Q




class JSONUploadForm(forms.Form):
    json_file = forms.FileField(
        label="Vyber JSON soubor",
        allow_empty_file=False,
        widget=forms.ClearableFileInput(attrs={"accept": ".json"}),
    )


class PartnerForm(forms.ModelForm):
    sekce_sekundarni = forms.ModelMultipleChoiceField(
        queryset=Sekce.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label="Doplňkové sekce",
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
        value = Decimal(str(value))
        return value.quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)

    def clean_latitude(self):
        value = self.cleaned_data["latitude"]
        value = Decimal(str(value))
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

    key_account_manager = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label="Key Account Manager",
        empty_label="--- Nerozhoduje ---",
    )

    # 💡 TADY UŽ JE TO SPRÁVNĚ:
    def get_filtered_queryset(self):
        queryset = Partner.objects.all()

        if self.cleaned_data.get("jmeno"):
            queryset = queryset.filter(jmeno__icontains=self.cleaned_data["jmeno"])

        if self.cleaned_data.get("mesto"):
            queryset = queryset.filter(mesto__icontains=self.cleaned_data["mesto"])

        if self.cleaned_data.get("cast_obce"):
            queryset = queryset.filter(
                cast_obce__icontains=self.cleaned_data["cast_obce"]
            )

        if self.cleaned_data.get("sekce"):
            queryset = queryset.filter(sekce=self.cleaned_data["sekce"])

        if self.cleaned_data.get("oslovovaci_poradi") is not None:
            queryset = queryset.filter(
                oslovovaci_poradi=self.cleaned_data["oslovovaci_poradi"]
            )

        if self.cleaned_data.get("created_by"):
            queryset = queryset.filter(created_by=self.cleaned_data["created_by"])

        if self.cleaned_data.get("kontaktovan") in ["True", "False"]:
            queryset = queryset.filter(
                kontaktovan=self.cleaned_data["kontaktovan"] == "True"
            )

        if self.cleaned_data.get("vysledek_kontaktu"):
            queryset = queryset.filter(
                vysledek_kontaktu__icontains=self.cleaned_data["vysledek_kontaktu"]
            )

        if self.cleaned_data.get("key_account_manager"):
            queryset = queryset.filter(
                key_account_manager=self.cleaned_data["key_account_manager"]
            )

        return queryset
