from django.urls import path
from . import vues_eleve

app_name = 'eleve'

urlpatterns = [
    path('tableau-de-bord/', vues_eleve.VueTableauDeBord.as_view(), name='tableau_de_bord'),
    
    # Navigation examen
    path('ecoles/', vues_eleve.VueChoisirEcole.as_view(), name='choisir_ecole'),
    path('ecoles/<int:ecole_id>/filieres/', vues_eleve.VueChoisirFiliere.as_view(), name='choisir_filiere'),
    path('filieres/<int:filiere_id>/epreuves/', vues_eleve.VueChoisirEpreuve.as_view(), name='choisir_epreuve'),
    path('epreuves/<int:epreuve_id>/cours/', vues_eleve.VueMiniCours.as_view(), name='mini_cours'),
    path('mes-resultats/', vues_eleve.VueMesResultats.as_view(), name='mes_resultats'),
    # Examen
    path('epreuves/<int:epreuve_id>/demarrer/', vues_eleve.VueDemarrerExamen.as_view(), name='demarrer_examen'),
    path('tentatives/<int:tentative_id>/question/<int:ordre>/', vues_eleve.VuePasserQuestion.as_view(), name='passer_question'),
    path('tentatives/<int:tentative_id>/terminer/', vues_eleve.VueTerminerExamen.as_view(), name='terminer_examen'),
    path('tentatives/<int:tentative_id>/resultat/', vues_eleve.VueResultatExamen.as_view(), name='resultat_examen'),
    # Parrainage
    path('parrainage/generer/',  vues_eleve.VueGenererCodeParrainage.as_view(), name='generer_parrainage'),
    path('mes-parrainages/',     vues_eleve.VueMesParrainages.as_view(),        name='mes_parrainages'),
]