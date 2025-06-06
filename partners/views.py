import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Count, Q
from django.contrib import messages
from .models import Partner, Sekce, KontaktHistorie
from .forms import PartnerForm, PartnerFilterForm
from django.views.decorators.http import require_GET
from django.db.models import OuterRef, Subquery
from decimal import Decimal, InvalidOperation
from .forms import JSONUploadForm


from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
from .forms import JSONUploadForm
from .models import Partner


def import_partners_view(request):
    if request.method == "POST":
        form = JSONUploadForm(request.POST, request.FILES)
        if form.is_valid():
            json_file = form.cleaned_data["json_file"]
            try:
                data = json.load(json_file)
                print(f"🔢 Celkem záznamů v souboru: {len(data)}")

                imported, skipped, errors = 0, 0, []
                skipped_entries = []

                for entry in data:
                    ico_raw = entry.get("ICO", "").strip()

                    if len(ico_raw) < 8:
                        errors.append(
                            f"{entry.get('Nazev', 'Neznámý')}: Neplatné ICO (méně než 8 znaků)"
                        )
                        continue

                    ico = ico_raw[:8]

                    if Partner.objects.filter(ICO=ico).exists():
                        skipped += 1
                        skipped_entries.append(entry.get("Nazev", "Neznámý"))
                        continue

                    try:
                        jmeno = entry.get("Nazev", "").strip()
                        adresa = entry.get("Adresa", "").strip()
                        web = entry.get("Web", "") or None
                        telefon = (
                            entry.get("Telefon", "")
                            .replace(",", "")
                            .replace(" ", "")
                            .strip()[:20]
                        )
                        email = entry.get("Email", "") or None
                        popis = entry.get("Popis", "")
                        lat_raw = entry.get("latitude", "").strip()
                        lon_raw = entry.get("longitude", "").strip()
                        latitude = Decimal(lat_raw)
                        longitude = Decimal(lon_raw)
                        mesto = entry.get("mesto", "").strip()
                        cast_obce = entry.get("cast_obce", "").strip()

                        partner = Partner.objects.create(
                            jmeno=jmeno,
                            jednatel=jmeno,
                            email=email,
                            telefon=telefon,
                            adresa=adresa,
                            latitude=latitude,
                            longitude=longitude,
                            web=web,
                            description=popis,
                            created_by_id=1,
                            ICO=ico,
                            mesto=mesto,
                            cast_obce=cast_obce,
                        )
                        imported += 1
                        messages.success(
                            request,
                            mark_safe(
                                f"✔️ Uložen partner: <a href='/admin/partners/partner/{partner.id}/change/' target='_blank'>{jmeno}</a>"
                            ),
                        )
                    except (InvalidOperation, Exception) as e:
                        errors.append(f"{jmeno}: {str(e)}")
                        continue

                messages.success(
                    request,
                    f"✅ Importováno: {imported}, přeskočeno: {skipped}, chyb: {len(errors)}",
                )

                if skipped_entries:
                    messages.info(request, f"🔁 Přeskočeno {skipped} duplicit:")
                    for name in skipped_entries:
                        messages.info(request, f"• {name}")

                if errors:
                    messages.warning(request, "❌ Některé záznamy měly chybu:")
                    for err in errors:
                        messages.warning(request, err)

                return redirect("import-partners")
            except Exception as e:
                messages.error(request, f"❌ Chyba při zpracování souboru: {str(e)}")
    else:
        form = JSONUploadForm()

    return render(request, "partners/import_partners.html", {"form": form})


@login_required
def pridat_partnera(request):
    if request.method == "POST":
        form = PartnerForm(request.POST)
        if form.is_valid():
            partner = form.save(commit=False)
            partner.created_by = request.user
            partner.save()
            
            messages.success(request, f"Byl úspěšně zadán partner {partner.jmeno}.")
            return redirect("novy_partner")
    else:
        form = PartnerForm()

    return render(request, "partners/pridat_partnera.html", {"form": form})


@login_required
def seznam_partneru(request):
    partner_list = Partner.objects.all()
    paginator = Paginator(partner_list, 25)
    page_number = request.GET.get("page")
    partneri = paginator.get_page(page_number)
    return render(request, "partners/seznam_partneru.html", {"partneri": partneri})


@login_required
def filtrovat_partnery(request):
    form = PartnerFilterForm(request.GET or None)
    partneri = Partner.objects.all()
    sekce_list = Sekce.objects.all()

    # Subquery pro poslední kontakt
    last_contact = KontaktHistorie.objects.filter(partner=OuterRef("pk")).order_by(
        "-datum"
    )
    partneri = partneri.annotate(
        posledni_datum=Subquery(last_contact.values("datum")[:1]),
        posledni_zpusob=Subquery(last_contact.values("zpusob")[:1]),
        posledni_vysledek=Subquery(last_contact.values("vysledek")[:1]),
        posledni_kontaktoval=Subquery(last_contact.values("kontaktoval__username")[:1]),
    )

    if form.is_valid():
        data = form.cleaned_data

        if data["jmeno"]:
            partneri = partneri.filter(jmeno__icontains=data["jmeno"])
        if data["mesto"]:
            partneri = partneri.filter(mesto__icontains=data["mesto"])
        if data["cast_obce"]:
            partneri = partneri.filter(cast_obce__icontains=data["cast_obce"])
        if data["sekce"]:
            partneri = partneri.filter(sekce_sekundarni=data["sekce"])
        if data["oslovovaci_poradi"] is not None:
            partneri = partneri.filter(oslovovaci_poradi=data["oslovovaci_poradi"])
        if data["created_by"]:
            partneri = partneri.filter(created_by=data["created_by"])
        if data["kontaktovan"] in ["True", "False"]:
            partneri = partneri.filter(kontaktovan=(data["kontaktovan"] == "True"))
        if data["vysledek_kontaktu"]:
            partneri = partneri.filter(
                vysledek_kontaktu__icontains=data["vysledek_kontaktu"]
            )
        if data["key_account_manager"]:
            partneri = partneri.filter(key_account_manager=data["key_account_manager"])

    # 🔥 Stránkování mimo if – musí fungovat vždy
    paginator = Paginator(partneri, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "partners/filtr_partneru.html",
        {
            "form": form,
            "partneri": page_obj,
            "sekce_list": sekce_list,
        },
    )


def home(request):
    uzivatele = User.objects.annotate(pocet_partneru=Count("partner"))
    return render(request, "partners/home.html", {"uzivatele": uzivatele})


@login_required
def editovat_partnera(request, pk):
    partner = get_object_or_404(Partner, pk=pk)
    if request.method == "POST":
        form = PartnerForm(request.POST, instance=partner)
        if form.is_valid():
            form.save()
            
            messages.success(request, f"Partner {partner.jmeno} byl aktualizován.")
            return redirect("filtr_partneru")
    else:
        if partner.longitude:
            partner.longitude = str(partner.longitude).rstrip("0").rstrip(".")
        if partner.latitude:
            partner.latitude = str(partner.latitude).rstrip("0").rstrip(".")

        form = PartnerForm(instance=partner)

    return render(request, "partners/editovat_partnera.html", {"form": form})


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
                "yellow"
                if partner.oslovovaci_poradi == 0
                else "green"
                if partner.oslovovaci_poradi == 1
                else "blue"
                if partner.oslovovaci_poradi == 2
                else "orange"
                if partner.oslovovaci_poradi == 3
                else "red"
            ),  # 🌈 Barevná logika
        }
        for partner in partneri
    ]

    return JsonResponse(data, safe=False)


@login_required
def mapa_partneru(request):
    form = PartnerFilterForm(request.GET or None)
    partneri = Partner.objects.all()

    if form.is_valid():
        if form.cleaned_data["jmeno"]:
            partneri = partneri.filter(jmeno__icontains=form.cleaned_data["jmeno"])
        if form.cleaned_data["mesto"]:
            partneri = partneri.filter(mesto__icontains=form.cleaned_data["mesto"])
        if form.cleaned_data["cast_obce"]:
            partneri = partneri.filter(
                cast_obce__icontains=form.cleaned_data["cast_obce"]
            )
        if form.cleaned_data["sekce"]:
            partneri = partneri.filter(sekce_sekundarni=form.cleaned_data["sekce"])
        if form.cleaned_data["oslovovaci_poradi"]:
            partneri = partneri.filter(
                oslovovaci_poradi=form.cleaned_data["oslovovaci_poradi"]
            )
        if form.cleaned_data["created_by"]:
            partneri = partneri.filter(created_by=form.cleaned_data["created_by"])
        if form.cleaned_data["kontaktovan"]:
            partneri = partneri.filter(
                kontaktovan=form.cleaned_data["kontaktovan"] == "True"
            )
        if form.cleaned_data["vysledek_kontaktu"]:
            partneri = partneri.filter(
                vysledek_kontaktu__icontains=form.cleaned_data["vysledek_kontaktu"]
            )
        if form.cleaned_data["key_account_manager"]:
            partneri = partneri.filter(
                key_account_manager=form.cleaned_data["key_account_manager"]
            )

    partneri_list = list(
        partneri.values(
            "id",
            "jmeno",
            "mesto",
            "cast_obce",
            "latitude",
            "longitude",
            "oslovovaci_poradi",
        )
    )

    for partner in partneri_list:
        partner_obj = partneri.get(id=partner["id"])
        partner["latitude"] = (
            float(partner_obj.latitude) if partner_obj.latitude else None
        )
        partner["longitude"] = (
            float(partner_obj.longitude) if partner_obj.longitude else None
        )

    return render(
        request,
        "partners/mapa_partneru.html",
        {"form": form, "partneri_json": json.dumps(partneri_list, ensure_ascii=False)},
    )


@login_required
def partner_detail(request, pk):
    partner = get_object_or_404(Partner, pk=pk)
    kontakty = KontaktHistorie.objects.filter(partner=partner).order_by("-datum")
    return render(
        request,
        "partners/partner_detail.html",
        {
            "partner": partner,
            "kontakty": kontakty,
        },
    )


@login_required
def smazat_partnera(request, pk):
    partner = get_object_or_404(Partner, pk=pk)
    if request.method == "POST":
        partner.delete()
        messages.success(request, "Partner byl úspěšně smazán.")
        return redirect("seznam_partneru")
    return render(request, "partners/smazat_partnera.html", {"partner": partner})


@login_required
def ulozit_poznamky(request, pk):
    partner = get_object_or_404(Partner, pk=pk)
    if request.method == "POST":
        partner.description = request.POST.get("description")
        partner.save()
        messages.success(request, "Poznámky byly uloženy.")
    return redirect("partner_detail", pk=partner.pk)


def check_ico(request):
    ico = request.GET.get("ico")
    exists = Partner.objects.filter(ICO=ico).exists()
    return JsonResponse({"exists": exists})


@require_GET
def ares_lookup(request):
    ico = request.GET.get("ico")
    if not ico or not ico.isdigit() or len(ico) != 8:
        return JsonResponse({"error": "Neplatné IČO"}, status=400)

    url = f"https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ico}"
    response = requests.get(url)

    if response.status_code != 200:
        return JsonResponse({"error": "Nepodařilo se připojit k ARES"}, status=500)

    data = response.json()

    if "obchodniJmeno" not in data:
        return JsonResponse({"error": "Subjekt s tímto IČO nebyl nalezen"}, status=404)

    vystup = {
        "jmeno": data.get("obchodniJmeno"),
        "adresa": data.get("sidlo", {}).get("textovaAdresa"),
        "mesto": data.get("sidlo", {}).get("nazevObce", ""),
    }
    return JsonResponse(vystup)


@login_required
def pridat_kontakt(request, pk):
    partner = get_object_or_404(Partner, pk=pk)
    if request.method == "POST":
        zpusob = request.POST.get("zpusob")
        vysledek = request.POST.get("vysledek")
        poznamka = request.POST.get("poznamka")

        # Vytvoříme nový kontakt
        kontakt = KontaktHistorie.objects.create(
            partner=partner,
            kontaktoval=request.user,
            zpusob=zpusob,
            vysledek=vysledek,
            poznamka=poznamka,
        )

        # Pokud výsledek je "uzavreno", nastavíme Key Account Managera
        if vysledek == "uzavreno":
            partner.key_account_manager = request.user
            partner.save()

        messages.success(request, "Záznam o kontaktu byl uložen.")
    return redirect("partner_detail", pk=pk)


def upravaPartneru(request):
    partners = Partner.objects.all().order_by("jmeno")
    paginator = Paginator(partners, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    if request.method == "POST":
        for partner in page_obj:
            partner_id = str(partner.id)
            partner.mesto = request.POST.get(f"mesto_{partner_id}", "")
            partner.cast_obce = request.POST.get(f"cast_{partner_id}", "")

            kam_id = request.POST.get(f"k_manager_{partner_id}")
            partner.key_account_manager = (
                User.objects.get(id=kam_id) if kam_id else None
            )

            sekce_ids = request.POST.getlist(f"sekce_{partner_id}[]")
            nove_sekce = Sekce.objects.filter(id__in=sekce_ids)

            partner.save()
            partner.sekce_sekundarni.set(nove_sekce)

        return redirect(request.path_info)

    vsechny_sekce = Sekce.objects.all()
    users = User.objects.all()

    return render(
        request,
        "partners/upravaPartneru.html",
        {
            "page_obj": page_obj,
            "vsechny_sekce": vsechny_sekce,
            "users": users,
        },
    )
