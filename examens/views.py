from django.shortcuts import render
from django.views import View

from .models import Ecole, Epreuve
from comptes.models import Eleve


class VueAccueil(View):
	def get(self, request):
		return render(request, 'accueil.html', {
			'ecoles': Ecole.objects.all()[:4],
			'total_eleves'   : Eleve.objects.count(),
			'total_epreuves' : Epreuve.objects.count(),
			'total_ecoles'   : Ecole.objects.count(),
		})
