from django.urls import path
from . import views

app_name = 'comptes'

urlpatterns = [
    path('connexion/',   views.VueConnexion.as_view(),   name='connexion'),
    path('deconnexion/', views.VueDeconnexion.as_view(), name='deconnexion'),
]