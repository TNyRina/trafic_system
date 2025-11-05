from django.shortcuts import render
from django.http import JsonResponse
from .models import Simulation
from django.conf import settings

# Crée une instance globale
simulation = Simulation(settings.CONFIG_FILE_SIMULATION)

def index(request):
    return render(request, "dashboard/carrefour.html")

def start_simulation(request):
    simulation.start_simulation()
    return JsonResponse({"status": "started"})

def carrefour_data(request):
    data = simulation.get_carrefour_data()
    return JsonResponse(data)
