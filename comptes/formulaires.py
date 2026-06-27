from django import forms


class FormulaireConnexion(forms.Form):

    identifiant      = forms.CharField(
                           label='Nom complet / Identifiant',
                           max_length=200,
                       )
    code_acces       = forms.CharField(
                           label="Mot de passe / Code d'accès",
                           max_length=200,
                       )
    code_parrainage  = forms.CharField(
                           label="Code parrainage (optionnel)",
                           max_length=50,
                           required=False,
                       )