from django.db import models
from .simulation_model import Simulation

class StatDirection(models.Model):
    """
    Statistiques par direction / voie (ex: véhicules par lane, temps moyen d'attente, etc.)
    """
    simulation = models.ForeignKey(
        Simulation,
        on_delete=models.CASCADE,
        related_name="stats_directions"
    )
    direction = models.CharField(max_length=20)  # ex: "N", "S", "E", "W" ou nom de lane
    nb_vehicules = models.IntegerField(default=0)
    temps_attente_moyen = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.direction} / Sim {self.simulation.id}"