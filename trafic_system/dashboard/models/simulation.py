import traci
import threading
import time
from django.utils import timezone
from .simulation_model import Simulation as DBSimulation
from .statistique import Statistique
from .carrefour import Carrefour
from .vehicle import Vehicle

class Simulation:
    def __init__(self, sumo_cfg):
        self.sumo_cfg = sumo_cfg
        self.carrefour = None
        self.running = False

        self.db_simulation = None

    def start_simulation(self):
        if self.running:
            # Simulation déjà lancée
            return

        try:
            self.db_simulation = DBSimulation.objects.create(
                date_debut=timezone.now(),
                nom="Simulation SUMO"
            )
            traci.simulation.getTime()
            print("Simulation déjà en cours")
            return
        except traci.exceptions.FatalTraCIError:
            pass

        self.running = True
        threading.Thread(target=self._run_sumo_gui).start()

    def get_carrefour_static_data(self):
        # Démarrer SUMO en mode non graphique (pour le serveur web)
        traci.start(["sumo", "-c", self.sumo_cfg])
        
        # Créer l'objet Carrefour
        carrefour = Carrefour()
        
        # Récupérer les informations
        edges_info = {
            "incomming" : {e: carrefour.get_edge_info(e) for e in carrefour.in_edges},
            "pedestrian" : {e: carrefour.get_edge_info(e) for e in carrefour.pedestrian_edges},
            "outgoing" : {e: carrefour.get_edge_info(e) for e in carrefour.out_edges},
            "internal" : {e: carrefour.get_edge_info(e) for e in carrefour.internal_edges}
            }
        lanes_info = {e: carrefour.get_lane_info(e) for e in carrefour.lanes}
        tl_state = carrefour.TL.get_info()
        pedestrian_lanes_info = carrefour.get_pedestrian_lanes_info()
        vehicles_per_lanes = carrefour.get_vehicle_counts_by_lane()
        
        # Fermer la simulation SUMO
        traci.close()

        return {
            "edges_info": edges_info,
            "lanes_info": lanes_info,
            "pedestrian_lanes_info": pedestrian_lanes_info,
            "vehicles_by_lanes": vehicles_per_lanes,
            "traffic_light_info": tl_state,
        }

    def _run_sumo_gui(self):
        try:
            traci.start(["sumo-gui", "-c", self.sumo_cfg])
            self.carrefour = Carrefour()

            while self.running:
                traci.simulationStep()
                time.sleep(0.1)

        except traci.exceptions.FatalTraCIError:
            print("SUMO GUI fermé, arrêt de la simulation.")
        finally:
            self.running = False
            try:
                traci.close()
            except:
                pass

    def stop_simulation(self):
        """
        Arrête proprement la simulation SUMO.
        Ferme la connexion TraCI et stoppe la boucle.
        Retourne les statistiques finales de la simulation.
        """
        self.running = False
        stats = {
            "simulation_id": getattr(self.db_simulation, "id", None),
            "nom": getattr(self.db_simulation, "nom", None),
            "date_debut": getattr(self.db_simulation, "date_debut", None),
            "date_fin": None,
            "time_simulation": -1,
            "nb_vehicules_total": 0,
            "nb_pietons_total": 0,
            "mean_speed_global": 0.0,
            "occupancy_global": 0.0,
            "directional_stats": {},
            "lanes_stats": {}
        }

        try:
            # Dernier step pour récupérer les stats finales
            try:
                stats["time_simulation"] = traci.simulation.getTime()
                stats["nb_vehicules_total"] = self.carrefour.get_total_vehicle_count()
                stats["nb_pietons_total"] = self.carrefour.get_total_pedestrian_count()

                stats["mean_speed_global"] = self.carrefour.get_mean_speed_global()
                stats["occupancy_global"] = self.carrefour.get_mean_occupancy_global()
                stats["lanes_stats"] = self.carrefour.get_vehicle_lanes_info()
                
                # Si tu as défini les directions N/S/E/W
                if hasattr(self, "directions"):
                    stats["directional_stats"] = self.carrefour.get_directional_stats(self.directions)

                # Mettre à jour la date de fin dans la simulation
                if self.db_simulation:
                    self.db_simulation.date_fin = timezone.now()
                    self.db_simulation.save()
                    stats["date_fin"] = self.db_simulation.date_fin

                # Sauvegarder les statistiques dans la base
                self._save_statistics(stats)

                # Dernier step (optionnel)
                traci.simulationStep()
            except Exception as e:
                print("Erreur lors de la récupération des stats finales :", e)

            # Essaye de fermer TraCI proprement
            traci.close(False)

        except Exception as e:
            print("Erreur lors de la fermeture de TraCI :", e)

        finally:
            self.running = False
            print("Simulation SUMO stoppée proprement.")

        return stats


    def _save_statistics(self, stats):
        """
        Sauvegarde les statistiques dans la base Django.
        """
        if not self.db_simulation:
            return

        try:
            Statistique.objects.create(
                simulation=self.db_simulation,
                duree_simulation=stats.get("time_simulation", 0),
                nb_vehicules_total=stats.get("nb_vehicules_total", 0),
                nb_pietons_total=stats.get("nb_pietons_total", 0),
                mean_speed_global=stats.get("mean_speed_global", 0.0),
                occupancy_global=stats.get("occupancy_global", 0.0),
                directional_stats=stats.get("directional_stats", {}),
                lanes_stats=stats.get("lanes_stats", {})
            )
            print(f"Statistiques sauvegardées pour la simulation {self.db_simulation.id}")
        except Exception as e:
            print("Erreur lors de la sauvegarde des statistiques :", e)



    def get_carrefour_data(self):
        if self.running:
            if self.carrefour:
                return {
                    "edges_info": {e: self.carrefour.get_edge_info(e) for e in self.carrefour.edges},
                    "lanes_info": {e: self.carrefour.get_lane_info(e) for e in self.carrefour.lanes},
                    "pedestrian_lanes_info": self.carrefour.get_pedestrian_lanes_info(),
                    "vehicles_by_lanes": self.carrefour.get_vehicle_counts_by_lane()
,
                    "traffic_light_info": self.carrefour.TL.get_info(),
                }
        return {
            "sumo": "inactive"
        }

    
    def stop_all_traffic_light(self):
        new_state = ''.join(['r' if c in ['g', 'G', 'y'] else c for c in self.carrefour.TL.get_state()])
        
        self.carrefour.TL.set_state(new_state)

        return self.get_carrefour_data()
    
    def restore_controle_tl(self):
        self.carrefour.TL.restore_controle()
        
        return self.get_carrefour_data()

    def prioritize_lane(self, lane_index):
        self.carrefour.TL.prioritize_lane(lane_index)

        return self.get_carrefour_data()
    
    def prioritize_lane_by_direction(self, direction):
        self.carrefour.TL.prioritize_lane_by_direction(direction)

        return self.get_carrefour_data()
    


    def change_phase_duration(self, index, duration):
        self.carrefour.TL.phase.set_phase_duration(index, duration)

        return self.get_carrefour_data()


    def change_phase_duration_by_group_yellow(self, new_duration):
        self.carrefour.TL.phase.set_phase_duration_by_group_yellow(new_duration)

        return self.get_carrefour_data()
    

    def change_phase_duration_by_group_green_main(self, new_duration):
        self.carrefour.TL.phase.set_phase_duration_by_group_green_main(new_duration)

        return self.get_carrefour_data()

    def change_phase_duration_by_group_green_short(self, new_duration):
        self.carrefour.TL.phase.set_phase_duration_by_group_green_short(new_duration)

        return self.get_carrefour_data()
    
    def create_vehicle(self, vehID, routeID):
        vehicle = Vehicle(vehID, routeID)
        vehicle.create_vehicle()

        return {
            "total_vehicle" : self.carrefour.get_total_vehicle_count()
        }
    

    def get_all_statistics(self):
        """
        Récupère toutes les statistiques des simulations dans la base de données.
        Retourne un dictionnaire avec l'ID de la simulation comme clé.
        """
        stats_dict = {}

        queryset = Statistique.objects.select_related('simulation').all().order_by('simulation__date_debut')

        for stat in queryset:
            stats_dict[stat.id] = {
                "simulation_id": stat.simulation.id, 
                "nom": getattr(stat.simulation, "nom", ""),
                "date_debut": stat.simulation.date_debut,
                "date_fin": stat.simulation.date_fin,
                "duree_simulation": stat.duree_simulation,
                "nb_vehicules_total": stat.nb_vehicules_total,
                "nb_pietons_total": stat.nb_pietons_total,
                "mean_speed_global": stat.mean_speed_global,
                "occupancy_global": stat.occupancy_global,
                "directional_stats": stat.directional_stats,
                "lanes_stats": stat.lanes_stats,
            }

        return stats_dict

    def delete_statistic(self, stat_id):
        """
        Supprime une statistique par son ID.
        Retourne un dictionnaire avec le résultat.
        """
        try:
            stat = Statistique.objects.get(id=stat_id)
            stat.delete()
            return {"success": True, "message": f"Statistique {stat_id} supprimée avec succès."}
        except Statistique.DoesNotExist:
            return {"success": False, "message": f"Statistique {stat_id} non trouvée."}
        except Exception as e:
            return {"success": False, "message": f"Erreur lors de la suppression : {str(e)}"}

    def get_statistics_by_date(self, start_date=None, end_date=None):
        """
        Récupère les statistiques filtrées par date ou plage de dates.
        
        Arguments:
            start_date (datetime ou date) : date/heure de début du filtre
            end_date (datetime ou date) : date/heure de fin du filtre
        
        Retourne :
            dict : { simulation_id: {...stats...} }
        """
        stats_dict = {}

        queryset = Statistique.objects.select_related('simulation').all()

        # Filtrage par date/heure
        if start_date and end_date:
            queryset = queryset.filter(simulation__date_debut__gte=start_date,
                                    simulation__date_debut__lte=end_date)
        elif start_date:
            queryset = queryset.filter(simulation__date_debut__gte=start_date)
        elif end_date:
            queryset = queryset.filter(simulation__date_debut__lte=end_date)

        queryset = queryset.order_by('simulation__date_debut')

        for stat in queryset:
            stats_dict[stat.simulation.id] = {
                "stat_id": stat.id,
                "nom": getattr(stat.simulation, "nom", ""),
                "date_debut": stat.simulation.date_debut,
                "date_fin": stat.simulation.date_fin,
                "duree_simulation": stat.duree_simulation,
                "nb_vehicules_total": stat.nb_vehicules_total,
                "nb_pietons_total": stat.nb_pietons_total,
                "mean_speed_global": stat.mean_speed_global,
                "occupancy_global": stat.occupancy_global,
                "directional_stats": stat.directional_stats,
                "lanes_stats": stat.lanes_stats,
            }

        return stats_dict