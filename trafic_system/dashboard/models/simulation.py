import traci
import threading
import time
from .carrefour import Carrefour
from .vehicle import Vehicle

class Simulation:
    def __init__(self, sumo_cfg):
        self.sumo_cfg = sumo_cfg
        self.carrefour = None
        self.running = False

    def start_simulation(self):
        if self.running:
            # Simulation déjà lancée
            return

        # Vérifier si traci est ouvert
        try:
            traci.simulation.getTime()
            # Si pas d'erreur, TraCI est actif
            print("Simulation déjà en cours")
            return
        except traci.exceptions.FatalTraCIError:
            # TraCI fermé, on peut relancer
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
        self.running = False

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
        traci.start(["sumo", "-c", self.sumo_cfg])
        
        carrefour = Carrefour()
        
        carrefour.TL.set_phase_duration(index, duration)
        
        traci.close()


        return self.get_carrefour_static_data()
    
    def create_vehicle(self, vehID, routeID):
        vehicle = Vehicle(vehID, routeID)
        vehicle.create_vehicle()

        return {
            "total_vehicle" : self.carrefour.get_total_vehicle_count()
        }