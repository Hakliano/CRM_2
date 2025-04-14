from django.db import models
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
    longitude = models.DecimalField(max_digits=9, decimal_places=8, blank=False, null=False)
    latitude = models.DecimalField(max_digits=9, decimal_places=8, blank=False, null=False)
    web = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    kontaktovan = models.BooleanField(default=False)
    vysledek_kontaktu = models.TextField(blank=True, null=True)
    sekce = models.ForeignKey('Sekce', on_delete=models.SET_DEFAULT, default=1)
    description = models.TextField(blank=True, null=True)
    ICO = models.CharField(blank=False, null=True, max_length=8, unique=True )


    def __str__(self):
        return self.jmeno


class Sekce(models.Model):
    nazev = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nazev