import traci
import threading
import time
from .carrefour import Carrefour

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
        threading.Thread(target=self._run_sumo).start()

    def _run_sumo(self):
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
        if self.carrefour:
            return {
                "traffic_light": self.carrefour.get_traffic_light_state(),
                "edges": {e: self.carrefour.get_edge_info(e) for e in self.carrefour.in_edges},
                "lanes": self.carrefour.get_incoming_lanes_info()
            }
        return {}
