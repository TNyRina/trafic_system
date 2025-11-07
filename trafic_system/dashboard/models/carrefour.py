import traci

class Carrefour:
    """
    Classe Carrefour SUMO pour récupérer toutes les informations utiles
    à la génération de traffic (voitures + piétons + feux).
    """

    def __init__(self, tl_id=None):
        self.tl_id = tl_id or traci.trafficlight.getIDList()[0]
        self.edges = traci.edge.getIDList()
        self.lanes = traci.lane.getIDList()

        # Séparation des edges
        self.internal_edges = [e for e in self.edges if e.startswith(':')]
        self.pedestrian_edges = [e for e in self.edges if '_w' in e.lower() or 'ped' in e.lower()]
        self.in_edges = [e for e in self.edges if '2' in e and e not in self.internal_edges + self.pedestrian_edges]
        self.out_edges = [e for e in self.edges if e not in self.internal_edges + self.pedestrian_edges + self.in_edges]

        # Mappage edge -> lanes
        self.edge_lanes = {edge: [lane for lane in self.lanes if lane.startswith(edge)] for edge in self.edges}

    # ==========================
    # Infos utiles pour la simulation
    # ==========================
    def get_edge_info(self, edge_id):
        """
        Retourne les infos utiles d'un edge pour générer le traffic
        """
        lanes = self.edge_lanes.get(edge_id, [])
        return {
            "id": edge_id,
            "num_lanes": len(lanes),
            "lane_ids": lanes,
            "length": traci.lane.getLength(lanes[0]) if lanes else 0,
            "max_speed": traci.lane.getMaxSpeed(lanes[0]) if lanes else 0
        }

    def get_lane_info(self, lane_id):
        """
        Infos utiles pour générer le traffic sur la lane
        """
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

    def get_vehicle_edges_info(self):
        """
        Retourne les edges véhicules entrants et leurs infos pour traffic
        """
        return {e: self.get_edge_info(e) for e in self.in_edges}

    def get_pedestrian_edges_info(self):
        """
        Retourne les edges piétons et leurs infos pour traffic
        """
        return {e: self.get_edge_info(e) for e in self.pedestrian_edges}

    def get_vehicle_lanes_info(self):
        """
        Retourne toutes les lanes véhicules utiles pour traffic
        """
        lanes = []
        for edge in self.in_edges + self.out_edges:
            lanes.extend(self.edge_lanes.get(edge, []))
        return {lane: self.get_lane_info(lane) for lane in lanes}

    def get_pedestrian_lanes_info(self):
        """
        Retourne toutes les lanes piétons pour traffic
        """
        lanes = []
        for edge in self.pedestrian_edges:
            lanes.extend(self.edge_lanes.get(edge, []))
        return {lane: self.get_lane_info(lane) for lane in lanes}

    # ==========================
    # Feux tricolores
    # ==========================
    def get_traffic_light_state(self):
        """
        État complet du feu principal avec infos dynamiques pour chaque lane.
        """
        logic = traci.trafficlight.getCompleteRedYellowGreenDefinition(self.tl_id)[0]
        state_str = traci.trafficlight.getRedYellowGreenState(self.tl_id)
        controlled_lanes = traci.trafficlight.getControlledLanes(self.tl_id)

        # Durée restante de la phase
        current_time = traci.simulation.getTime()
        next_switch = traci.trafficlight.getNextSwitch(self.tl_id)
        remaining_time = next_switch - current_time

        # Signification des feux
        meanings = {
            "r": "Rouge (interdiction totale)",
            "y": "Jaune (transition)",
            "g": "Vert (autorisation partielle)",
            "G": "Vert (prioritaire)",
            "s": "Stop/Clignotement",
            "O": "Aucun signal",
            "p": "Piétons : passage autorisé",
            "P": "Piétons : arrêt obligatoire",
        }

        lanes_info = {}
        for lane, sig in zip(controlled_lanes, state_str):
            lanes_info[lane] = {
                "id": lane,
                "signal": sig,
                "meaning": meanings.get(sig, f"Inconnu ({sig})"),
                "num_vehicles": traci.lane.getLastStepVehicleNumber(lane),
                "vehicle_ids": traci.lane.getLastStepVehicleIDs(lane),
                "occupancy": traci.lane.getLastStepOccupancy(lane),
                "mean_speed": traci.lane.getLastStepMeanSpeed(lane),
                "waiting_time": traci.lane.getWaitingTime(lane)
            }

        return {
            "tl_id": self.tl_id,
            "phase": traci.trafficlight.getPhase(self.tl_id),
            "remaining_time": remaining_time,
            "code": state_str,
            "type": self._get_traffic_light_type_name(logic.type),
            "lanes": lanes_info
        }


    def _get_traffic_light_type_name(self, tl_type):
        type_map = {
            0: "static",
            1: "actuated",
            2: "delay_based",
            3: "external",
            4: "nema",
            5: "swarm",
            6: "rail_signal"
        }
        return type_map.get(tl_type, f"inconnu ({tl_type})")

    # ==========================
    # Comptages dynamiques
    # ==========================
    def get_vehicle_counts_by_lane(self):
        """
        Retourne le nombre de véhicules par lane pour les lanes véhicules
        """
        vehicle_lanes = []
        for edge in self.in_edges + self.out_edges:
            vehicle_lanes.extend(self.edge_lanes.get(edge, []))
        
        return {lane: traci.lane.getLastStepVehicleNumber(lane) for lane in vehicle_lanes}

    def get_pedestrian_counts_by_lane(self):
        """
        Retourne le nombre de piétons par lane pour les lanes piétons
        """
        ped_lanes = []
        for edge in self.pedestrian_edges:
            ped_lanes.extend(self.edge_lanes.get(edge, []))
        
        return {lane: traci.lane.getLastStepVehicleNumber(lane) for lane in ped_lanes}