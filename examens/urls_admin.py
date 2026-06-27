from django.urls import path
from . import vues_admin

app_name = 'admin_examens'

urlpatterns = [
    path('tableau-de-bord/', vues_admin.VueTableauDeBord.as_view(), name='tableau_de_bord'),

    # Écoles
    path('ecoles/',                    vues_admin.VueListeEcoles.as_view(),    name='ecoles_liste'),
    path('ecoles/ajouter/',            vues_admin.VueAjouterEcole.as_view(),   name='ecole_ajouter'),
    path('ecoles/<int:ecole_id>/modifier/',  vues_admin.VueModifierEcole.as_view(),  name='ecole_modifier'),
    path('ecoles/<int:ecole_id>/supprimer/', vues_admin.VueSupprimerEcole.as_view(), name='ecole_supprimer'),

    # Filières
    path('filieres/',                      vues_admin.VueListeFilieres.as_view(),    name='filieres_liste'),
    path('filieres/ajouter/',              vues_admin.VueAjouterFiliere.as_view(),   name='filiere_ajouter'),
    path('filieres/<int:filiere_id>/modifier/',  vues_admin.VueModifierFiliere.as_view(),  name='filiere_modifier'),
    path('filieres/<int:filiere_id>/supprimer/', vues_admin.VueSupprimerFiliere.as_view(), name='filiere_supprimer'),

    # Épreuves
    path('epreuves/',                      vues_admin.VueListeEpreuves.as_view(),    name='epreuves_liste'),
    path('epreuves/ajouter/',              vues_admin.VueAjouterEpreuve.as_view(),   name='epreuve_ajouter'),
    path('epreuves/<int:epreuve_id>/modifier/',  vues_admin.VueModifierEpreuve.as_view(),  name='epreuve_modifier'),
    path('epreuves/<int:epreuve_id>/supprimer/', vues_admin.VueSupprimerEpreuve.as_view(), name='epreuve_supprimer'),

    # Questions (placeholder, on le fera juste après)
    path('epreuves/<int:epreuve_id>/questions/', vues_admin.VueQuestionsEpreuve.as_view(), name='epreuve_questions'),
        path('epreuves/<int:epreuve_id>/questions/<int:question_id>/supprimer/',
            vues_admin.VueSupprimerQuestion.as_view(), name='question_supprimer'),
        # Élèves
        path('eleves/',                        vues_admin.VueListeEleves.as_view(),         name='eleves_liste'),
        path('eleves/ajouter/',                vues_admin.VueAjouterEleve.as_view(),        name='eleve_ajouter'),
        path('eleves/<int:eleve_id>/statut/',  vues_admin.VueBasculerStatutEleve.as_view(), name='eleve_statut'),
        path('eleves/<int:eleve_id>/supprimer/', vues_admin.VueSupprimerEleve.as_view(),    name='eleve_supprimer'),

    # Parrainages
    path('parrainages/',                          vues_admin.VueParrainagesAdmin.as_view(),  name='parrainages'),
    path('parrainages/<int:eleve_id>/bonus-paye/', vues_admin.VueMarquerBonusPaye.as_view(), name='bonus_paye'),
]