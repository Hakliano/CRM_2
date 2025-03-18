import json
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Count, Q
from django.contrib import messages
from .models import Partner
from .forms import PartnerForm, PartnerFilterForm


@login_required
def pridat_partnera(request):
    if request.method == 'POST':
        form = PartnerForm(request.POST)
        if form.is_valid():
            partner = form.save(commit=False)
            partner.created_by = request.user
            partner.save()
            messages.success(request, f"Byl úspěšně zadán partner {partner.jmeno}.")
            return redirect('novy_partner')
    else:
        form = PartnerForm()
    
    return render(request, 'partners/pridat_partnera.html', {'form': form})

@login_required
def seznam_partneru(request):
    partner_list = Partner.objects.all()
    paginator = Paginator(partner_list, 25)  
    page_number = request.GET.get('page')
    partneri = paginator.get_page(page_number)  
    return render(request, 'partners/seznam_partneru.html', {'partneri': partneri})

@login_required
def filtrovat_partnery(request):
    form = PartnerFilterForm(request.GET or None)
    partneri = Partner.objects.all()

    if form.is_valid():
        if form.cleaned_data['jmeno']:
            partneri = partneri.filter(jmeno__icontains=form.cleaned_data['jmeno'])
        if form.cleaned_data['mesto']:
            partneri = partneri.filter(mesto__icontains=form.cleaned_data['mesto'])
        if form.cleaned_data['cast_obce']:
            partneri = partneri.filter(cast_obce__icontains=form.cleaned_data['cast_obce'])
        if form.cleaned_data['sekce']:
            partneri = partneri.filter(sekce=form.cleaned_data['sekce'])
        if form.cleaned_data['oslovovaci_poradi']:
            partneri = partneri.filter(oslovovaci_poradi=form.cleaned_data['oslovovaci_poradi'])
        if form.cleaned_data['created_by']:
            partneri = partneri.filter(created_by=form.cleaned_data['created_by'])
        if form.cleaned_data['kontaktovan']:
            partneri = partneri.filter(kontaktovan=form.cleaned_data['kontaktovan'] == 'True')
        if form.cleaned_data['vysledek_kontaktu']:
            partneri = partneri.filter(vysledek_kontaktu__icontains=form.cleaned_data['vysledek_kontaktu'])
        if form.cleaned_data['ICO']:
            partneri = partneri.filter(ICO=form.cleaned_data['ICO'] == 'True')

    return render(request, 'partners/filtr_partneru.html', {'form': form, 'partneri': partneri})

def home(request):
    uzivatele = User.objects.annotate(pocet_partneru=Count('partner'))
    return render(request, 'partners/home.html', {'uzivatele': uzivatele})

@login_required
def editovat_partnera(request, pk):
    partner = get_object_or_404(Partner, pk=pk)
    if request.method == 'POST':
        form = PartnerForm(request.POST, instance=partner)
        if form.is_valid():
            form.save()
            messages.success(request, f"Partner {partner.jmeno} byl aktualizován.")
            return redirect('filtr_partneru')
    else:
        form = PartnerForm(instance=partner)

    return render(request, 'partners/editovat_partnera.html', {'form': form})

@login_required
def partneri_json(request):
    partneri = Partner.objects.exclude(latitude__isnull=True, longitude__isnull=True)

    data = [
        {
            "id": partner.id,
            "jmeno": partner.jmeno,
            "latitude": partner.latitude,
            "longitude": partner.longitude,
            "mesto": partner.mesto,
            "cast_obce": partner.cast_obce,
            "sekce": partner.sekce.nazev if partner.sekce else "Neurčeno",
            "barva": (
                "yellow" if partner.oslovovaci_poradi == 0 else
                "green" if partner.oslovovaci_poradi == 1 else
                "blue" if partner.oslovovaci_poradi == 2 else
                "orange" if partner.oslovovaci_poradi == 3 else
                "red"
            )  # 🌈 Barevná logika
        }
        for partner in partneri
    ]

    return JsonResponse(data, safe=False)


@login_required
def mapa_partneru(request):
    form = PartnerFilterForm(request.GET or None)
    partneri = Partner.objects.all()

    if form.is_valid():
        if form.cleaned_data['jmeno']:
            partneri = partneri.filter(jmeno__icontains=form.cleaned_data['jmeno'])
        if form.cleaned_data['mesto']:
            partneri = partneri.filter(mesto__icontains=form.cleaned_data['mesto'])
        if form.cleaned_data['cast_obce']:
            partneri = partneri.filter(cast_obce__icontains=form.cleaned_data['cast_obce'])
        if form.cleaned_data['sekce']:
            partneri = partneri.filter(sekce=form.cleaned_data['sekce'])
        if form.cleaned_data['oslovovaci_poradi']:
            partneri = partneri.filter(oslovovaci_poradi=form.cleaned_data['oslovovaci_poradi'])
        if form.cleaned_data['created_by']:
            partneri = partneri.filter(created_by=form.cleaned_data['created_by'])
        if form.cleaned_data['kontaktovan']:
            partneri = partneri.filter(kontaktovan=form.cleaned_data['kontaktovan'] == 'True')
        if form.cleaned_data['vysledek_kontaktu']:
            partneri = partneri.filter(vysledek_kontaktu__icontains=form.cleaned_data['vysledek_kontaktu'])

    partneri_list = list(partneri.values('id', 'jmeno', 'mesto', 'cast_obce', 'latitude', 'longitude', 'oslovovaci_poradi'))
    
    for partner in partneri_list:
        partner_obj = partneri.get(id=partner['id'])  
        partner['latitude'] = float(partner_obj.latitude) if partner_obj.latitude else None
        partner['longitude'] = float(partner_obj.longitude) if partner_obj.longitude else None

    return render(request, 'partners/mapa_partneru.html', {
        'form': form,
        'partneri_json': json.dumps(partneri_list, ensure_ascii=False) 
    })



@login_required
def partner_detail(request, pk):
    partner = get_object_or_404(Partner, pk=pk)
    return render(request, 'partners/partner_detail.html', {'partner': partner})

@login_required
def smazat_partnera(request, pk):
    partner = get_object_or_404(Partner, pk=pk)
    if request.method == 'POST':
        partner.delete()
        messages.success(request, "Partner byl úspěšně smazán.")
        return redirect('seznam_partneru')
    return render(request, 'partners/smazat_partnera.html', {'partner': partner})


@login_required
def ulozit_poznamky(request, pk):
    partner = get_object_or_404(Partner, pk=pk)
    if request.method == "POST":
        partner.description = request.POST.get('description')
        partner.save()
        messages.success(request, "Poznámky byly uloženy.")
    return redirect('partner_detail', pk=partner.pk)