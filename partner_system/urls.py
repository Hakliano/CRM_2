from django.contrib import admin
from django.urls import path, include
from partners import views as partner_views 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('partners/', include('partners.urls')),
    path('', partner_views.home, name='home'),
]
