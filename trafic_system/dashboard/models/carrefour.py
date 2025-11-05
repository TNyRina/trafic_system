import traci

class Carrefour:
    def __init__(self, tl_id=None):
        """
        Initialisation du carrefour.
        - tl_id : ID du feu de circulation principal. Si None, récupère automatiquement le premier feu.
        """
        # Récupère le feu principal
        self.tl_id = tl_id or traci.trafficlight.getIDList()[0]
        
        # Récupère tous les edges
        self.edges = traci.edge.getIDList()
        
        # Sépare edges entrantes (commencent par '-') et sortantes
        self.in_edges = [e for e in self.edges if e.startswith('-')]
        self.out_edges = [e for e in self.edges if not e.startswith('-') and not e.startswith(':')]
        self.internal_edges = [e for e in self.edges if e.startswith(':')]
        
        # Récupère toutes les lanes
        self.lanes = traci.lane.getIDList()
        
        # Lier les lanes à chaque edge
        self.edge_lanes = {}
        for edge in self.edges:
            self.edge_lanes[edge] = [lane for lane in self.lanes if lane.startswith(edge)]

    # --- Informations sur les edges ---
    def get_edge_info(self, edge_id):
        lanes = self.edge_lanes[edge_id]
        first_lane = lanes[0] if lanes else None
        if first_lane:
            length = traci.lane.getLength(first_lane)
            max_speed = traci.lane.getMaxSpeed(first_lane)
        else:
            length = 0
            max_speed = 0

        return {
            "length": length,
            "max_speed": max_speed,
            "num_vehicles": sum(traci.lane.getLastStepVehicleNumber(l) for l in lanes),
            "vehicles": sum([list(traci.lane.getLastStepVehicleIDs(l)) for l in lanes], []),
            "num_lanes": len(lanes)
        }
    # --- Informations sur les lanes ---
    def get_lane_info(self, lane_id):
        return {
            "length": traci.lane.getLength(lane_id),
            "max_speed": traci.lane.getMaxSpeed(lane_id),
            "num_vehicles": traci.lane.getLastStepVehicleNumber(lane_id),
            "vehicles": traci.lane.getLastStepVehicleIDs(lane_id),
            "occupancy": traci.lane.getLastStepOccupancy(lane_id),
            "mean_speed": traci.lane.getLastStepMeanSpeed(lane_id),
            "shape": traci.lane.getShape(lane_id)
        }

    # --- Infos pour toutes les lanes entrantes ---
    def get_incoming_lanes_info(self):
        info = {}
        for edge in self.in_edges:
            for lane in self.edge_lanes[edge]:
                info[lane] = self.get_lane_info(lane)
        return info

    # --- Compter véhicules par edge ou lane ---
    def count_vehicles_edges(self):
        return {e: traci.edge.getLastStepVehicleNumber(e) for e in self.in_edges}

    def count_vehicles_lanes(self):
        info = {}
        for edge in self.in_edges:
            for lane in self.edge_lanes[edge]:
                info[lane] = traci.lane.getLastStepVehicleNumber(lane)
        return info

    # --- Gestion du feu ---
    def get_traffic_light_state(self):
        return traci.trafficlight.getRedYellowGreenState(self.tl_id)

    def set_traffic_light_state(self, state):
        """
        state : chaîne de caractères comme 'GrGr' ou 'rGrG' suivant le réseau
        """
        traci.trafficlight.setRedYellowGreenState(self.tl_id, state)
