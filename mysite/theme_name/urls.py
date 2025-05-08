from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    # Main website URLs
    path("", views.home, name="home"),
    path('admin/', admin.site.urls),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-use/', views.terms_of_use, name='terms_of_use'),
    path("blog/", views.blog_list, name="blog_list"),
    path("blog/<int:pk>/", views.blog_detail, name="blog_detail"),
    path("nucp/", RedirectView.as_view(url="https://nucp.ca", permanent=True), name="nucp"),
    path('registration/', views.registration_view, name='registration'),
    path('prescription/', views.prescription_view, name='prescription'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_selection, name='register_selection'),
    path('register/patient/', views.patient_registration, name='patient_registration'),
    path('register/provider/', views.provider_registration, name='provider_registration'),
    path('registration/success/', views.registration_success, name='registration_success'),
    path('schedule-demo/', views.schedule_demo, name='schedule_demo'),
    path('logout/', views.logout_view, name='logout'),
    
    # Include other app URLs with appropriate prefixes
    path('patient-dashboard/', include('patient.urls')),
    path('provider-dashboard/', include('provider.urls')),
    path('admin-dashboard/', include('admin_portal.urls')),
]
