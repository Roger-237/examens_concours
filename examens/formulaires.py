from django import forms
from django.forms import inlineformset_factory
from .models import Ecole, Filiere, Epreuve, Question, Choix, ConcoursBlanc
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


# ─────────────────────────────────────────
#  CONCOURS BLANC
# ─────────────────────────────────────────
class FormulaireConcoursBlanc(forms.ModelForm):

    epreuve_1 = forms.ModelChoiceField(
        queryset=Epreuve.objects.all(),
        label='Épreuve 1',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    epreuve_2 = forms.ModelChoiceField(
        queryset=Epreuve.objects.all(),
        label='Épreuve 2',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    epreuve_3 = forms.ModelChoiceField(
        queryset=Epreuve.objects.all(),
        label='Épreuve 3',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model  = ConcoursBlanc
        fields = ['ecole', 'titre', 'heure_debut', 'heure_fin', 'nb_places_max']
        widgets = {
            'ecole': forms.Select(attrs={'class': 'form-select'}),
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Grand Concours Blanc INPTIC 2026'}),
            'heure_debut': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'heure_fin': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'nb_places_max': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 100'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        ep1 = cleaned_data.get('epreuve_1')
        ep2 = cleaned_data.get('epreuve_2')
        ep3 = cleaned_data.get('epreuve_3')

        if ep1 and ep2 and ep3:
            if len({ep1.id, ep2.id, ep3.id}) < 3:
                raise forms.ValidationError("Les 3 épreuves doivent être différentes.")

        h_debut = cleaned_data.get('heure_debut')
        h_fin   = cleaned_data.get('heure_fin')
        if h_debut and h_fin and h_fin <= h_debut:
            raise forms.ValidationError("L'heure de fin doit être postérieure à l'heure de début.")

        return cleaned_data


class FormulaireInscriptionConcours(forms.Form):

    nom = forms.CharField(
        label='Votre Nom complet',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Entrez votre Nom complet (ex: Jean Dupont)',
            'required': True,
        })
    )