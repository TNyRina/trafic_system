import traci
from .traffic_light import TrafficLight

class Carrefour:
    """
    Classe Carrefour SUMO pour récupérer toutes les informations utiles
    à la génération de traffic (voitures + piétons + feux), ainsi que
    des statistiques dynamiques (vitesse, occupation, comptage).
    """

    def __init__(self, tl_id=None):
        self.TL = TrafficLight()

        self.edges = traci.edge.getIDList()
        self.lanes = traci.lane.getIDList()

        # Séparation des edges
        self.internal_edges = [e for e in self.edges if e.startswith(':')]
        self.pedestrian_edges = [e for e in self.edges if '_w' in e.lower() or 'ped' in e.lower()]
        self.in_edges = [e for e in self.edges
                         if ('2C' in e or '_toC' in e) and e not in self.internal_edges + self.pedestrian_edges]
        self.out_edges = [e for e in self.edges
                          if e not in self.internal_edges + self.pedestrian_edges + self.in_edges]

        # Mappage edge -> lanes
        self.edge_lanes = {edge: [lane for lane in self.lanes if lane.startswith(edge)] for edge in self.edges}

        # Lanes véhicules et piétons
        self.vehicle_lanes = [lane for edge in self.in_edges + self.out_edges for lane in self.edge_lanes.get(edge, [])]
        self.pedestrian_lanes = [lane for edge in self.pedestrian_edges for lane in self.edge_lanes.get(edge, [])]

    # ==========================
    # Infos statiques
    # ==========================
    def get_edge_info(self, edge_id):
        lanes = self.edge_lanes.get(edge_id, [])
        return {
            "id": edge_id,
            "num_lanes": len(lanes),
            "lane_ids": lanes,
            "length": traci.lane.getLength(lanes[0]) if lanes else 0,
            "max_speed": traci.lane.getMaxSpeed(lanes[0]) if lanes else 0
        }

    def get_lane_info(self, lane_id):
        return {
            "id": lane_id,
            "edge_id": traci.lane.getEdgeID(lane_id),
            "length": traci.lane.getLength(lane_id),
            "max_speed": traci.lane.getMaxSpeed(lane_id),
            "num_vehicles": traci.lane.getLastStepVehicleNumber(lane_id),
            "vehicle_ids": traci.lane.getLastStepVehicleIDs(lane_id),
            "occupancy": traci.lane.getLastStepOccupancy(lane_id),
            "mean_speed": traci.lane.getLastStepMeanSpeed(lane_id),
            "waiting_time": traci.lane.getWaitingTime(lane_id)
        }

    # ==========================
    # Infos lanes véhicules/piétons (compatibilité)
    # ==========================
    def get_vehicle_lanes_info(self):
        return {lane: self.get_lane_info(lane) for lane in self.vehicle_lanes}

    def get_pedestrian_lanes_info(self):
        return {lane: self.get_lane_info(lane) for lane in self.pedestrian_lanes}

    # ==========================
    # Infos edges véhicules/piétons
    # ==========================
    def get_vehicle_edges_info(self):
        return {e: self.get_edge_info(e) for e in self.in_edges}

    def get_pedestrian_edges_info(self):
        return {e: self.get_edge_info(e) for e in self.pedestrian_edges}

    # ==========================
    # Comptages dynamiques
    # ==========================
    def get_vehicle_counts_by_lane(self):
        return {lane: traci.lane.getLastStepVehicleNumber(lane) for lane in self.vehicle_lanes}

    def get_pedestrian_counts_by_lane(self):
        return {lane: traci.lane.getLastStepVehicleNumber(lane) for lane in self.pedestrian_lanes}

    def get_total_vehicle_count(self):
        return sum(self.get_vehicle_counts_by_lane().values())

    def get_total_pedestrian_count(self):
        return sum(self.get_pedestrian_counts_by_lane().values())

    # ==========================
    # Statistiques globales
    # ==========================
    def get_mean_speed_global(self):
        if not self.vehicle_lanes:
            return 0
        total_speed = sum(traci.lane.getLastStepMeanSpeed(lane) for lane in self.vehicle_lanes)
        return total_speed / len(self.vehicle_lanes)

    def get_mean_occupancy_global(self):
        if not self.vehicle_lanes:
            return 0
        total_occupancy = sum(traci.lane.getLastStepOccupancy(lane) for lane in self.vehicle_lanes)
        return total_occupancy / len(self.vehicle_lanes)

    # ==========================
    # Statistiques par direction (optionnel)
    # ==========================
    def get_directional_stats(self, directions: dict):
        """
        directions = {
            'N': ['edge1','edge2'],
            'S': ['edge3','edge4'],
            ...
        }
        Retourne la vitesse moyenne et l'occupation par direction.
        """
        stats = {}
        for dir_name, dir_edges in directions.items():
            lanes = [lane for edge in dir_edges for lane in self.edge_lanes.get(edge, [])]
            if lanes:
                mean_speed = sum(traci.lane.getLastStepMeanSpeed(lane) for lane in lanes) / len(lanes)
                mean_occupancy = sum(traci.lane.getLastStepOccupancy(lane) for lane in lanes) / len(lanes)
            else:
                mean_speed = 0
                mean_occupancy = 0
            stats[dir_name] = {"mean_speed": mean_speed, "mean_occupancy": mean_occupancy}
        return stats
