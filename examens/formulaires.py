from django import forms
from django.forms import inlineformset_factory
from .models import Ecole, Filiere, Epreuve, Question, Choix
from comptes.models import Eleve, Utilisateur, Role, generer_code_acces


# ─────────────────────────────────────────
#  ÉCOLE
# ─────────────────────────────────────────
class FormulaireEcole(forms.ModelForm):

    class Meta:
        model  = Ecole
        fields = ['nom', 'logo']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : INPTIC, INSG, ITO, IST...'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
            }),
        }
# ─────────────────────────────────────────
#  FILIÈRE
# ─────────────────────────────────────────
class FormulaireFiliere(forms.ModelForm):

    class Meta:
        model  = Filiere
        fields = ['nom', 'ecole']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : Génie Informatique, Économie...'
            }),
            'ecole': forms.Select(attrs={
                'class': 'form-select',
            }),
        }


# ─────────────────────────────────────────
#  ÉPREUVE
# ─────────────────────────────────────────
class FormulaireEpreuve(forms.ModelForm):

    class Meta:
        model  = Epreuve
        fields = ['filiere', 'titre', 'annee', 'mini_cours']
        widgets = {
            'filiere': forms.Select(attrs={
                'class': 'form-select',
            }),
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : Concours d\'entrée — Mathématiques'
            }),
            'annee': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : 2025'
            }),
            'mini_cours': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Cours à lire avant de commencer l\'examen. Vous pouvez utiliser des formules LaTeX entre $...$ pour les maths.'
            }),
        }
 
# ─────────────────────────────────────────
#  QUESTION + CHOIX (Formsets)
# ─────────────────────────────────────────
class FormulaireQuestion(forms.ModelForm):

    class Meta:
        model  = Question
        fields = ['texte', 'ordre']
        widgets = {
            'texte': forms.Textarea(attrs={
                'class': 'form-control question-texte',
                'rows': 2,
                'placeholder': 'Texte de la question (formules LaTeX entre $...$)'
            }),
            'ordre': forms.NumberInput(attrs={
                'class': 'form-control',
                'style': 'width:80px;'
            }),
        }


class FormulaireChoix(forms.ModelForm):

    class Meta:
        model  = Choix
        fields = ['texte', 'est_correct']
        widgets = {
            'texte': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Texte du choix'
            }),
            'est_correct': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }


# Formset des choix liés à une question (4 choix par défaut)
ChoixFormSet = inlineformset_factory(
    Question, Choix,
    form=FormulaireChoix,
    extra=4,
    max_num=4,
    can_delete=True,
)


# ─────────────────────────────────────────
#  ÉLÈVE
# ─────────────────────────────────────────
class FormulaireEleve(forms.Form):

    nom_complet = forms.CharField(
        label='Nom complet',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex : Jean Dupont'
        })
    )