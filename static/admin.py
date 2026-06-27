from django.contrib import admin

# Register your models here.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Role


@admin.register(Utilisateur)
class AdministrateurUtilisateur(UserAdmin):

    # ── Colonnes affichées dans la liste ──
    list_display   = ['email', 'prenom', 'nom', 'role', 'est_verifie', 'is_active', 'date_inscription']
    list_filter    = ['role', 'est_verifie', 'is_active']
    search_fields  = ['email', 'nom', 'prenom']
    ordering       = ['-date_inscription']

    # ── Détail d'un utilisateur ──
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('email', 'nom', 'prenom', 'nationalite', 'telephone')
        }),
        ('Rôle & Accès', {
            'fields': ('role', 'is_active', 'is_staff', 'est_verifie')
        }),
        ('Permissions', {
            'fields': ('is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)   # ← réduit par défaut
        }),
        ('Dates', {
            'fields': ('last_login', 'date_inscription'),
        }),
    )

    # ── Formulaire création d'un utilisateur ──
    add_fieldsets = (
        ('Nouvel utilisateur', {
            'fields': ('email', 'nom', 'prenom', 'role', 'password1', 'password2')
        }),
    )

    readonly_fields = ['date_inscription', 'last_login']

    # ── Champ username remplacé par email ──
    USERNAME_FIELD = 'email'