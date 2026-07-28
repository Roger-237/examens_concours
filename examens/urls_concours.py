from django.urls import path
from . import vues_concours

app_name = 'concours'

urlpatterns = [
    path('',                        vues_concours.VueAccueilConcours.as_view(),    name='accueil'),
    path('inscription/',            vues_concours.VueInscriptionConcours.as_view(),name='inscription'),
    path('passer/',                 vues_concours.VuePasserConcours.as_view(),     name='passer'),
    path('passer/<uuid:token>/',    vues_concours.VuePasserConcours.as_view(),     name='passer_token'),
    path('fin/',                    vues_concours.VueFinConcours.as_view(),        name='fin'),
    path('fin/<uuid:token>/',       vues_concours.VueFinConcours.as_view(),        name='fin_token'),
    path('classement/<int:concours_id>/', vues_concours.VueClassementConcours.as_view(), name='classement_detail'),
    path('classement/',             vues_concours.VueClassementConcours.as_view(), name='classement'),
]
