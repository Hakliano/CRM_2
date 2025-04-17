from django.contrib import admin
from .models import Partner, Sekce
from .forms import PartnerForm

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    form = PartnerForm
    list_display = ('jmeno', 'mesto', 'sekce')
    search_fields = ('jmeno', 'mesto', 'sekce__nazev')

@admin.register(Sekce)
class SekceAdmin(admin.ModelAdmin):
    list_display = ('nazev',) 
    search_fields = ('nazev',)