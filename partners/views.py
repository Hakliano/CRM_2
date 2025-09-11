import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Count, Q, OuterRef, Subquery, F, OrderBy

from django.contrib import messages
from .models import Partner, Sekce, KontaktHistorie
from .forms import PartnerForm, PartnerFilterForm, JSONUploadForm
from django.views.decorators.http import require_GET
from decimal import Decimal, InvalidOperation
from math import ceil
from django.utils.safestring import mark_safe

@login_required
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
    partneri = Partner.objects.all().select_related("sekce", "key_account_manager", "created_by")
    sekce_list = Sekce.objects.all()

    # POSLEDNÍ kontakt daného partnera (jednoznačně dle data a id)
    last_contact = KontaktHistorie.objects.filter(
        partner=OuterRef("pk")
    ).order_by("-datum", "-id")

    partneri = partneri.annotate(
        posledni_kontakt_id=Subquery(last_contact.values("id")[:1]),
        posledni_datum=Subquery(last_contact.values("datum")[:1]),
        posledni_zpusob=Subquery(last_contact.values("zpusob")[:1]),
        posledni_vysledek=Subquery(last_contact.values("vysledek")[:1]),
        posledni_kontaktoval=Subquery(last_contact.values("kontaktoval__username")[:1]),
    )

    # ✅ VŽDY mít 'data' – i když form.is_valid() vrátí False
    data = form.cleaned_data if form.is_valid() else {}

    # --- běžné filtry (nekontaktní) ---
    if data.get("jmeno"):
        partneri = partneri.filter(jmeno__icontains=data["jmeno"])
    if data.get("mesto"):
        partneri = partneri.filter(mesto__icontains=data["mesto"])
    if data.get("cast_obce"):
        partneri = partneri.filter(cast_obce__icontains=data["cast_obce"])
    if data.get("sekce"):
        partneri = partneri.filter(sekce_sekundarni=data["sekce"])
    if data.get("oslovovaci_poradi") is not None and data.get("oslovovaci_poradi") != "":
        partneri = partneri.filter(oslovovaci_poradi=data["oslovovaci_poradi"])
    if data.get("created_by"):
        partneri = partneri.filter(created_by=data["created_by"])
    if data.get("key_account_manager"):
        partneri = partneri.filter(key_account_manager=data["key_account_manager"])

    # ✅ FILTR POUZE podle POSLEDNÍHO kontaktu (aktuální stav)
    if data.get("posledni_vysledek"):
        partneri = partneri.filter(
            kontakty__id=F("posledni_kontakt_id"),
            kontakty__vysledek=data["posledni_vysledek"],
        )

    # ✅ „Kontaktován“ = existence posledního kontaktu
    if data.get("kontaktovan") in ["True", "False"]:
        # True  -> poslední_kontakt existuje (isnull=False)
        # False -> poslední_kontakt neexistuje (isnull=True)
        partneri = partneri.filter(posledni_kontakt_id__isnull=(data["kontaktovan"] != "True"))

    # řazení: nejnovější poslední kontakt první, bez „díry“ pro NULL
    partneri = partneri.order_by(
        OrderBy(F("posledni_datum"), descending=True, nulls_last=True),
        "-id",
    )

    # stránkování
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
            "vysledky_kontaktu": KontaktHistorie.VYSLEDKY_KONTAKTU,
        },
    )





def home(request):
    statuses = [code for code, _ in KontaktHistorie.VYSLEDKY_KONTAKTU]
    labels = dict(KontaktHistorie.VYSLEDKY_KONTAKTU)

    last_contact = KontaktHistorie.objects.filter(
        partner=OuterRef("pk")
    ).order_by("-datum", "-id")

    # anotujeme poslední výsledek a spočteme
    qs = Partner.objects.annotate(
        last_vysledek=Subquery(last_contact.values("vysledek")[:1])
    )

    raw = qs.values("last_vysledek").annotate(cnt=Count("id"))

    counts = {code: 0 for code in statuses}
    no_contact = 0
    for r in raw:
        key = r["last_vysledek"]
        if key is None:
            no_contact = r["cnt"]
        elif key in counts:
            counts[key] = r["cnt"]

    total = qs.count()
    rows = [(code, labels[code], counts[code]) for code in statuses]

   
    statuses = [code for code, _ in KontaktHistorie.VYSLEDKY_KONTAKTU]
    labels = dict(KontaktHistorie.VYSLEDKY_KONTAKTU)

    last_contact = KontaktHistorie.objects.filter(
        partner=OuterRef("pk")
    ).order_by("-datum", "-id")

    qs = Partner.objects.annotate(
        last_vysledek=Subquery(last_contact.values("vysledek")[:1])
    )
    raw = qs.values("last_vysledek").annotate(cnt=Count("id"))

    counts = {code: 0 for code in statuses}
    no_contact = 0
    for r in raw:
        key = r["last_vysledek"]
        if key is None:
            no_contact = r["cnt"]
        elif key in counts:
            counts[key] = r["cnt"]

    total = qs.count()
    rows = [(code, labels[code], counts[code]) for code in statuses]

    # --- NOVÉ: procentuální „úspěšnost“ ---
    zakladna = (
        counts.get("nezajem", 0)
        + counts.get("no_time", 0)
        + counts.get("nevi", 0)
        + counts.get("schuzka", 0)
        + counts.get("zajem", 0)
        + counts.get("uzavreno", 0)
        + counts.get("predbezny", 0)
    )
    pozitivni = (
        counts.get("schuzka", 0)
        + counts.get("zajem", 0)
        + counts.get("uzavreno", 0)
        + counts.get("predbezny", 0)
    )
    if zakladna > 0:
        pct = (pozitivni / zakladna) * 100.0
        # zaokrouhlit NAHORU na 1 desetinné místo
        pct_ceil_1 = ceil(pct * 10) / 10.0
    else:
        pct_ceil_1 = 0.0

    return render(
        request,
        "partners/home.html",
        {
            "rows": rows,
            "no_contact": no_contact,
            "total": total,
            "success_base": zakladna,
            "success_pos": pozitivni,
            "success_pct": f"{pct_ceil_1:.1f}",  # připravené k přímému zobrazení
        },
    )


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
                else "black"
                if partner.oslovovaci_poradi == 4
                else "turquoise"
                if partner.oslovovaci_poradi == 5
                else "brown"
                if partner.oslovovaci_poradi == 6
                else "gold"
                if partner.oslovovaci_poradi == 7
                else "violet"
                if partner.oslovovaci_poradi == 8
                else "red"
                if partner.oslovovaci_poradi == 9
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

    # ✅ bezpečné načtení dat i když form.is_valid() == False
    data = form.cleaned_data if form.is_valid() else {}

    # --- vaše původní filtry, jen bezpečně přes .get() ---
    if data.get("jmeno"):
        partneri = partneri.filter(jmeno__icontains=data["jmeno"])

    if data.get("mesto"):
        partneri = partneri.filter(mesto__icontains=data["mesto"])

    if data.get("cast_obce"):
        partneri = partneri.filter(cast_obce__icontains=data["cast_obce"])

    if data.get("sekce"):
        partneri = partneri.filter(sekce_sekundarni=data["sekce"])

    if data.get("oslovovaci_poradi"):
        partneri = partneri.filter(oslovovaci_poradi=data["oslovovaci_poradi"])

    if data.get("created_by"):
        partneri = partneri.filter(created_by=data["created_by"])

    if data.get("kontaktovan") in ["True", "False"]:
        partneri = partneri.filter(kontaktovan=(data["kontaktovan"] == "True"))

    # ⚠️ kompatibilita: pokud tohle pole ve formu nemáte, .get(...) vrátí None a filtr se neaplikuje
    if data.get("vysledek_kontaktu"):
        partneri = partneri.filter(
            vysledek_kontaktu__icontains=data["vysledek_kontaktu"]
        )

    if data.get("key_account_manager"):
        partneri = partneri.filter(key_account_manager=data["key_account_manager"])

    # --- výstup pro mapu (beze změny struktury) ---
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

    # převod Decimal -> float pro JS bez dalších DB dotazů
    for p in partneri_list:
        p["latitude"] = float(p["latitude"]) if p["latitude"] is not None else None
        p["longitude"] = float(p["longitude"]) if p["longitude"] is not None else None

    return render(
        request,
        "partners/mapa_partneru.html",
        {
            "form": form,
            "partneri_json": json.dumps(partneri_list, ensure_ascii=False),
        },
    )



@login_required
def partner_detail(request, pk):
    partner = get_object_or_404(Partner, pk=pk)

    # ✅ rychlá změna oslovovacího pořadí přímo z detailu
    if request.method == "POST" and request.POST.get("akce") == "zmena_poradi":
        val = request.POST.get("oslovovaci_poradi")
        try:
            n = int(val)
        except (TypeError, ValueError):
            messages.error(request, "Zadejte prosím číslo 0–9.")
            return redirect("partner_detail", pk=pk)

        if n < 0 or n > 9:
            messages.error(request, "Oslovovací pořadí musí být v rozsahu 0–9.")
            return redirect("partner_detail", pk=pk)

        if partner.oslovovaci_poradi != n:
            partner.oslovovaci_poradi = n
            partner.save(update_fields=["oslovovaci_poradi"])
            messages.success(request, f"Oslovovací pořadí bylo změněno na {n}.")
        else:
            messages.info(request, "Oslovovací pořadí zůstalo beze změny.")

        return redirect("partner_detail", pk=pk)

    # standardní render detailu
    kontakty = KontaktHistorie.objects.filter(partner=partner).order_by("-datum")
    return render(
        request,
        "partners/partner_detail.html",
        {"partner": partner, "kontakty": kontakty},
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

@login_required
def upravaPartneru(request):
    # --- FILTR: město (GET ?mesto=...) ---
    selected_mesto = (request.GET.get("mesto") or "").strip()

    partners = Partner.objects.all().order_by("jmeno")

    # Podpora "Prázdno" = __EMPTY__  -> mesto IS NULL nebo ""
    if selected_mesto == "__EMPTY__":
        partners = partners.filter(Q(mesto__isnull=True) | Q(mesto__exact=""))
    elif selected_mesto:
        partners = partners.filter(mesto__icontains=selected_mesto)

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

        # Zachovej aktuální filtr i stránku po uložení
        qs = request.GET.copy()
        qs["page"] = page_obj.number
        return redirect(f"{request.path}?{qs.urlencode()}")

    vsechny_sekce = Sekce.objects.all()
    users = User.objects.all()

    # Seznam měst pro select (distinct, bez prázdných)
    mesta = (
        Partner.objects.exclude(mesto__isnull=True)
        .exclude(mesto__exact="")
        .values_list("mesto", flat=True)
        .distinct()
        .order_by("mesto")
    )
    # Přidáme syntetickou volbu "__EMPTY__" pro "Prázdno"
    mesta = ["__EMPTY__"] + list(mesta)

    return render(
        request,
        "partners/upravaPartneru.html",
        {
            "page_obj": page_obj,
            "vsechny_sekce": vsechny_sekce,
            "users": users,
            "mesta": mesta,
            "selected_mesto": selected_mesto,
        },
    )


@login_required
def callscripty(request):
    return render(request, "partners/callscripty.html")
