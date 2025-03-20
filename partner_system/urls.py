from django.contrib import admin
from django.urls import path, include
from partners import views as partner_views 
from django.contrib.auth import views as auth_views
from partners import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('partners/', include('partners.urls')),
    path('', partner_views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='partners/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('seznam/', views.seznam_partneru, name='seznam_partneru'),

]
