from django.db import models


class Simulation(models.Model):
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    nom = models.CharField(max_length=100, default="Simulation SUMO")

    def __str__(self):
        return f"Simulation {self.id} - {self.date_debut.strftime('%Y-%m-%d %H:%M:%S')}"