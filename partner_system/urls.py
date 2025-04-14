from django.contrib import admin
from django.urls import path, include
from partners import views as partner_views 
from django.contrib.auth import views as auth_views
from partners import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('partners.urls')),
    path('', partner_views.home, name='home'),
    path('check-ico/', partner_views.check_ico, name='check_ico'), 
    path('ares-lookup/', partner_views.ares_lookup, name='ares_lookup'),
]
