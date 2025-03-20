from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('novy-partner/', views.pridat_partnera, name='novy_partner'),
    path('seznam/', views.seznam_partneru, name='seznam_partneru'),
    path('filtr/', views.filtrovat_partnery, name='filtr_partneru'),
    path('', views.home, name='home'),
    path('editovat/<int:pk>/', views.editovat_partnera, name='editovat_partnera'),
    path('api/partneri/', views.partneri_json, name='partneri_json'),
    path('mapa/', views.mapa_partneru, name='mapa_partneru'),
    path('partner/<int:pk>/', views.partner_detail, name='partner_detail'),
    path('partner/<int:pk>/smazat/', views.smazat_partnera, name='smazat_partnera'),
    path('partner/<int:pk>/ulozit_poznamky/', views.ulozit_poznamky, name='ulozit_poznamky'),
    path('login/', auth_views.LoginView.as_view(template_name='partners/login.html'), name='login'),
]
