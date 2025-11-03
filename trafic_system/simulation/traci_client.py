import traci

class SumoController:
    def __init__(self, config_path, gui=False):  # Ajouter gui ici
        sumo_binary = "sumo-gui" if gui else "sumo"
        traci.start([sumo_binary, "-c", config_path])

    def set_phase(self, traffic_light_id, phase_index):
        traci.trafficlight.setPhase(traffic_light_id, phase_index)

    def get_phase(self, traffic_light_id):
        return traci.trafficlight.getPhase(traffic_light_id)

    def get_vehicle_count(self, edge_id):
        return traci.edge.getLastStepVehicleNumber(edge_id)

    def step(self):
        traci.simulationStep()

    def close(self):
        traci.close()
