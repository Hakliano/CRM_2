from django.contrib import admin
from .models import Partner, Sekce, KontaktHistorie
from .forms import PartnerForm


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    form = PartnerForm
    list_display = ("jmeno", "mesto", "sekce")
    search_fields = ("jmeno", "mesto", "sekce__nazev")

    def get_readonly_fields(self, request, obj=None):
        return super().get_readonly_fields(request, obj) + (
            "display_formatted_longitude",
            "display_formatted_latitude",
        )

    def display_formatted_longitude(self, obj):
        return format(obj.longitude.normalize(), "f")

    def display_formatted_latitude(self, obj):
        return format(obj.latitude.normalize(), "f")

    display_formatted_longitude.short_description = "Formatted Longitude"
    display_formatted_latitude.short_description = "Formatted Latitude"


@admin.register(Sekce)
class SekceAdmin(admin.ModelAdmin):
    list_display = ("nazev",)
    search_fields = ("nazev",)


@admin.register(KontaktHistorie)
class KontaktHistorieAdmin(admin.ModelAdmin):
    list_display = ['partner', 'datum', 'zpusob', 'vysledek', 'kontaktoval']
    list_filter = ['zpusob', 'vysledek', 'kontaktoval']