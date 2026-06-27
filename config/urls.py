from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from examens.views import VueAccueil
from comptes.views import VuePrivacyPolicy
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('privacy-policy/', VuePrivacyPolicy.as_view(), name='privacy_policy'),
    path('', VueAccueil.as_view(), name='accueil'),
    path('django-admin/', admin.site.urls),
    path('auth/',         include('comptes.urls',        namespace='comptes')),
    path('admin/',        include('examens.urls_admin',  namespace='admin_examens')),
    path('eleve/',        include('examens.urls_eleve',  namespace='eleve')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)