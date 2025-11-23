from django.db import models
from .simulation_model import Simulation

class Statistique(models.Model):
    simulation = models.OneToOneField(
        Simulation,
        on_delete=models.CASCADE,
        related_name="stat"
    )

    # Informations générales
    duree_simulation = models.FloatField(help_text="Durée totale (secondes)")

    # Trafic général
    nb_vehicules_total = models.IntegerField(default=0)
    nb_pietons_total = models.IntegerField(default=0)

    # Stats globales
    mean_speed_global = models.FloatField(default=0.0, help_text="Vitesse moyenne globale des voies")
    occupancy_global = models.FloatField(default=0.0, help_text="Occupation moyenne globale des voies")

    # Stats par direction (optionnel)
    directional_stats = models.JSONField(
        default=dict,
        help_text="Stats par direction: { 'N': {'mean_speed':..., 'occupancy':...}, ... }"
    )

    # Stats par lane (optionnel)
    lanes_stats = models.JSONField(
        default=dict,
        help_text="Stats détaillées par lane: { 'lane_id': {'num_vehicles':..., 'mean_speed':..., 'occupancy':...}, ... }"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Stat Simulation {self.simulation.id}"
