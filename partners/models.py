from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User


class Partner(models.Model):
    jmeno = models.CharField(max_length=255)
    jednatel = models.CharField(max_length=255)
    email = models.EmailField()
    telefon = models.CharField(max_length=20)
    adresa = models.CharField(max_length=255)
    mesto = models.CharField(max_length=100)
    cast_obce = models.CharField(max_length=100, blank=True, null=True)
    oslovovaci_poradi = models.IntegerField(default=0)
    key_account_manager = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='klienti')
    longitude = models.DecimalField(
        max_digits=50, decimal_places=45, blank=False, null=False
    )
    latitude = models.DecimalField(
        max_digits=50, decimal_places=45, blank=False, null=False
    )
    web = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    kontaktovan = models.BooleanField(default=False)
    vysledek_kontaktu = models.TextField(blank=True, null=True)
    sekce = models.ForeignKey("Sekce", on_delete=models.SET_DEFAULT, default=1)
    sekce_sekundarni = models.ManyToManyField("Sekce", blank=True, related_name="partneri_sekundarni")
    description = models.TextField(blank=True, null=True)
    ICO = models.CharField(blank=False, null=True, max_length=8, unique=True)

    def __str__(self):
        return self.jmeno

    @admin.display(description='Formatted Longitude')
    def formatted_longitude(self):
        return format(self.longitude.normalize(), "f")

    @admin.display(description='Formatted Latitude')
    def formatted_latitude(self):
        return format(self.latitude.normalize(), "f")


class Sekce(models.Model):
    nazev = models.CharField(max_length=100)

    def __str__(self):
        return self.nazev


class PartnerSection(models.Model):
    partner = models.ForeignKey("Partner", on_delete=models.CASCADE)
    sekce = models.ForeignKey("Sekce", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("partner", "sekce")

    def __str__(self):
        return f"{self.partner.jmeno} – {self.sekce.nazev}"


class KontaktHistorie(models.Model):
    ZPUSOBY_KONTAKTU = [
        ('telefon', 'Telefon'),
        ('osobne', 'Osobně'),
        ('email', 'E-mail'),
        ('sms', 'SMS'),
        ('jinak', 'Jinak'),
    ]

    VYSLEDKY_KONTAKTU = [
        ('nezajem', 'Nemá zájem'),
        ('schuzka', 'Domluvená schůzka'),
        ('zajem', 'Má zájem'),
        ('uzavreno', 'Obchod uzavřen'),
        ('free_ucet', 'Free účet'),
    ]

    partner = models.ForeignKey("Partner", on_delete=models.CASCADE, related_name="kontakty")
    kontaktoval = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    datum = models.DateTimeField(auto_now_add=True)
    zpusob = models.CharField(max_length=20, choices=ZPUSOBY_KONTAKTU)
    vysledek = models.CharField(max_length=20, choices=VYSLEDKY_KONTAKTU)
    poznamka = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-datum"]

    def __str__(self):
        return f"{self.partner.jmeno} – {self.get_zpusob_display()} ({self.get_vysledek_display()}) – {self.datum.date()}"
       