import json
from django.shortcuts import render
from django.http import JsonResponse
from .models import Simulation
from django.conf import settings

# Crée une instance globale
simulation = Simulation(settings.CONFIG_FILE_SIMULATION)

def index(request):
    context = simulation.get_carrefour_static_data()
    return JsonResponse(context)

def start_simulation(request):
    simulation.start_simulation()
    return JsonResponse({"status": "started"})

def carrefour_data(request):
    data = simulation.get_carrefour_data()
    return JsonResponse(data)

def stop_all_tl(request):
    data = simulation.stop_all_traffic_light()
    return JsonResponse(data)

def restore_controle_tl(request):
    data = simulation.restore_controle_tl()
    return JsonResponse(data)

def prioritize_lane(request, lane):
    if lane is None or lane == "":
        return JsonResponse({"error": "Paramètre 'lane' manquant"}, status=400)
    result = simulation.prioritize_lane(lane)
    
    return JsonResponse(result)

def prioritize_lane_by_direction(request, direction):
    if direction is None or direction == "":
        return JsonResponse({"error": "Paramètre 'direction' manquant"}, status=400)
    result = simulation.prioritize_lane_by_direction(direction)
    
    return JsonResponse(result)

def change_phase_duration(request, phase_index, duration):
    result = simulation.change_phase_duration(phase_index, duration)

    return JsonResponse(result)

def create_vehicle(request, vehicleID, routeID):
    result = simulation.create_vehicle(vehicleID, routeID)

    return JsonResponse(result)