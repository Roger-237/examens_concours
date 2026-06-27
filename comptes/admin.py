from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Eleve, Role


# ─────────────────────────────────────────
#  UTILISATEUR
# ─────────────────────────────────────────
@admin.register(Utilisateur)
class AdministrateurUtilisateur(UserAdmin):

    list_display   = ['username', 'role', 'is_active', 'date_inscription']
    list_filter    = ['role', 'is_active']
    search_fields  = ['username']
    ordering       = ['-date_inscription']

    fieldsets = (
        ('Informations', {
            'fields': ('username', 'password', 'role')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('last_login', 'date_inscription'),
        }),
    )

    add_fieldsets = (
        ('Nouvel utilisateur', {
            'fields': ('username', 'role', 'password1', 'password2')
        }),
    )

    readonly_fields = ['date_inscription', 'last_login']


# ─────────────────────────────────────────
#  ÉLÈVE
# ─────────────────────────────────────────
@admin.register(Eleve)
class AdministrateurEleve(admin.ModelAdmin):

    list_display   = ['nom_complet', 'code_acces', 'statut', 'empreinte_device', 'date_inscription']
    list_filter    = ['statut']
    search_fields  = ['nom_complet', 'code_acces']
    ordering       = ['-date_inscription']
    readonly_fields = ['code_acces', 'empreinte_device', 'date_inscription']