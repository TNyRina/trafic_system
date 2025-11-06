import traci


class Carrefour:
    """
    Classe de gestion d’un carrefour SUMO (voitures + piétons + feux).
    Fournit des méthodes pour analyser les edges, lanes et feux de circulation.
    """

    def __init__(self, tl_id=None):
        """
        Initialise le carrefour et récupère les entités principales.
        :param tl_id: ID du feu de circulation principal (si None, le premier est pris)
        """
        self.tl_id = tl_id or traci.trafficlight.getIDList()[0]

        # Récupération des edges
        self.edges = traci.edge.getIDList()
        self.in_edges = [e for e in self.edges if e.startswith('-')]
        self.out_edges = [e for e in self.edges if not e.startswith('-') and not e.startswith(':')]
        self.internal_edges = [e for e in self.edges if e.startswith(':')]
        self.ped_edges = [e for e in self.edges if 'ped' in e.lower() or e in self.internal_edges]

        # Récupération des lanes et mappage edge → lanes
        self.lanes = traci.lane.getIDList()
        self.edge_lanes = {
            edge: [lane for lane in self.lanes if lane.startswith(edge)]
            for edge in self.edges
        }

    # =========================================================
    # ===     INFOS EDGES / LANES / PIÉTONS               ====
    # =========================================================

    def get_edge_info(self, edge_id):
        """
        Retourne les informations d’un edge : longueur, vitesse, véhicules, etc.
        """
        lanes = self.edge_lanes.get(edge_id, [])
        first_lane = lanes[0] if lanes else None

        length = traci.lane.getLength(first_lane) if first_lane else 0
        max_speed = traci.lane.getMaxSpeed(first_lane) if first_lane else 0

        # Agrégation des véhicules sur toutes les lanes de l’edge
        all_vehicles = []
        for l in lanes:
            all_vehicles.extend(traci.lane.getLastStepVehicleIDs(l))

        return {
            "id": edge_id,
            "length": length,
            "max_speed": max_speed,
            "num_vehicles": len(all_vehicles),
            "vehicles": all_vehicles,
            "num_lanes": len(lanes)
        }

    def get_lane_info(self, lane_id):
        """
        Retourne les informations d’une lane : longueur, vitesse, occupation, etc.
        """
        return {
            "id": lane_id,
            "edgeId": traci.lane.getEdgeID(lane_id),
            "length": traci.lane.getLength(lane_id),
            "max_speed": traci.lane.getMaxSpeed(lane_id),
            "num_vehicles": traci.lane.getLastStepVehicleNumber(lane_id),
            "vehicles": traci.lane.getLastStepVehicleIDs(lane_id),
            "occupancy": traci.lane.getLastStepOccupancy(lane_id),
            "mean_speed": traci.lane.getLastStepMeanSpeed(lane_id),
            "shape": traci.lane.getShape(lane_id),
        }

    def get_incoming_lanes_info(self):
        """
        Retourne les informations pour toutes les lanes entrantes.
        """
        return {
            lane: self.get_lane_info(lane)
            for edge in self.in_edges
            for lane in self.edge_lanes.get(edge, [])
        }

    def get_pedestrian_lanes_info(self):
        """
        Retourne les informations pour les lanes piétonnes.
        """
        info = {}
        for edge in self.ped_edges:
            for lane in self.edge_lanes.get(edge, []):
                info[lane] = {
                    "length": traci.lane.getLength(lane),
                    "num_pedestrians": traci.lane.getLastStepVehicleNumber(lane),  # piétons = "vehicules"
                    "pedestrian_ids": traci.lane.getLastStepVehicleIDs(lane),
                    "occupancy": traci.lane.getLastStepOccupancy(lane)
                }
        return info

    # =========================================================
    # ===     COMPTAGES RAPIDES                             ====
    # =========================================================

    def count_vehicles_edges(self):
        """Retourne le nombre de véhicules par edge entrant."""
        return {e: traci.edge.getLastStepVehicleNumber(e) for e in self.in_edges}

    def count_vehicles_lanes(self):
        """Retourne le nombre de véhicules par lane entrante."""
        return {
            lane: traci.lane.getLastStepVehicleNumber(lane)
            for edge in self.in_edges
            for lane in self.edge_lanes.get(edge, [])
        }

    # =========================================================
    # ===     FEUX DE CIRCULATION                           ====
    # =========================================================

    def get_traffic_light_state(self):
        """
        Retourne l’état actuel du feu de circulation principal :
        - code brut (rGy...)
        - état détaillé
        - type de feu (static, actuated, external, etc.)
        """
        logic = traci.trafficlight.getCompleteRedYellowGreenDefinition(self.tl_id)[0]
        return {
            "code": traci.trafficlight.getRedYellowGreenState(self.tl_id),
            "detail": self.get_traffic_light_detailed_state(),
            "type": self._get_traffic_light_type_name(logic.type)
        }

    def get_traffic_light_detailed_state(self):
        """
        Retourne l’état interprété du feu pour chaque lane contrôlée.
        """
        state_str = traci.trafficlight.getRedYellowGreenState(self.tl_id)
        controlled_lanes = traci.trafficlight.getControlledLanes(self.tl_id)

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

        return {
            lane: meanings.get(sig, f"Inconnu ({sig})")
            for lane, sig in zip(controlled_lanes, state_str)
        }

    def get_pedestrian_traffic_light_state(self):
        """
        Retourne l’état des feux piétons uniquement.
        """
        full_state = traci.trafficlight.getRedYellowGreenState(self.tl_id)
        controlled_lanes = traci.trafficlight.getControlledLanes(self.tl_id)
        return {
            lane: sig for lane, sig in zip(controlled_lanes, full_state)
            if 'ped' in lane.lower() or lane.startswith(':')
        }

    def set_traffic_light_state(self, state):
        """
        Modifie l’état du feu (exemple : 'GrGr' ou 'rGrG').
        """
        traci.trafficlight.setRedYellowGreenState(self.tl_id, state)

    # =========================================================
    # ===     MÉTHODES INTERNES / UTILITAIRES              ====
    # =========================================================

    def _get_traffic_light_type_name(self, tl_type):
        """
        Traduit le code numérique du type de feu en texte lisible.
        """
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
