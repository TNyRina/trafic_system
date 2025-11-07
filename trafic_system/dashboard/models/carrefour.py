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
        return traci.trafficlight.getRedYellowGreenState(self.tl_id)
    
    def set_traffic_light_state(self, state):
        traci.trafficlight.setRedYellowGreenState(self.tl_id, state)
    
    def restore_tl_controle(self):
        traci.trafficlight.setProgram(self.tl_id, 0)

    def prioritize_lane(self, lane_index):
        controlled_lanes = traci.trafficlight.getControlledLanes(self.tl_id)
    
        state = list(traci.trafficlight.getRedYellowGreenState(self.tl_id))
        
        # Vérifier la taille
        if lane_index < 0 or lane_index >= len(state):
            print(f"Erreur : lane_index {lane_index} hors limite ({len(state)})")
            return {"error": "lane_index hors limite"}
        
        new_state = []
        for i in range(len(state)):
            if i == lane_index:
                new_state.append("G")  # vert pour lane prioritaire
            else:
                # Vérifier si c'est un passage piéton
                if controlled_lanes[i].startswith(":"):
                    new_state.append("r")  # ou "p" selon SUMO
                else:
                    new_state.append("r")  # rouge pour les autres lanes

        traci.trafficlight.setRedYellowGreenState(self.tl_id, "".join(new_state))
        
    
    def get_traffic_light_info(self):
        """
        État complet du feu principal avec infos dynamiques pour chaque lane.
        """
        logic = traci.trafficlight.getCompleteRedYellowGreenDefinition(self.tl_id)[0]

        state_str = self.get_traffic_light_state()
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
        for i,(lane, sig) in enumerate(zip(controlled_lanes, state_str)):
            lname = lane.lower()
            direction = "inconnue"
            type_voie = "vehicule"

            # --- Détection du type ---
            if "_w" in lname or "ped" in lname:
                type_voie = "pieton"

            # --- Détection direction selon le nom ---
            if "n2" in lname or lname.startswith("n_"):
                direction = "nord"
            elif "s2" in lname or lname.startswith("s_"):
                direction = "sud"
            elif "e2" in lname or lname.startswith("e_"):
                direction = "est"
            elif "w2" in lname or lname.startswith("w_"):
                direction = "ouest"

            # --- Détection direction spéciale pour piétons (traversée) ---
            if type_voie == "pieton":
                if "n_w" in lname or "n2s" in lname or "n2s_w" in lname:
                    direction = "nord_sud"
                elif "s_w" in lname or "s2n" in lname or "s2n_w" in lname:
                    direction = "sud_nord"
                elif "e_w" in lname or "e2w" in lname or "e2w_w" in lname:
                    direction = "est_ouest"
                elif "w_e" in lname or "w2e" in lname or "w2e_w" in lname:
                    direction = "ouest_est"
                
            
            lanes_info[lane] = {
                "index": i,
                "id": lane,
                "type": type_voie,
                "direction": direction,
                "signal": sig,
                "meaning": meanings.get(sig, f"Inconnu ({sig})"),
                "num_vehicles": traci.lane.getLastStepVehicleNumber(lane),
                "vehicle_ids": traci.lane.getLastStepVehicleIDs(lane),
                "occupancy": traci.lane.getLastStepOccupancy(lane),
                "mean_speed": traci.lane.getLastStepMeanSpeed(lane),
                "waiting_time": traci.lane.getWaitingTime(lane)
            }

        # Phase duration
        phases = logic.getPhases()
        current_phase_index = traci.trafficlight.getPhase(self.tl_id)
        current_phase = phases[current_phase_index]
        phase_duration = current_phase.duration

        # Phases info
        logic_list = traci.trafficlight.getCompleteRedYellowGreenDefinition(self.tl_id)
    
        # Transformer les objets Logic en dictionnaires
        logics_serialized = []
        for logic in logic_list:
            logics_serialized.append({
                "programID": logic.programID,
                "type": self._get_traffic_light_type_name(logic.type),
                "currentPhaseIndex": logic.currentPhaseIndex,
                "phases": [
                    {
                        "duration": phase.duration,
                        "state": phase.state,
                        "minDur": getattr(phase, "minDur", None),
                        "maxDur": getattr(phase, "maxDur", None),
                    }
                    for phase in logic.phases
                ]
            })

        return {
            "tl_id": self.tl_id,
            "phase": traci.trafficlight.getPhase(self.tl_id),
            "duration": phase_duration,
            "remaining_time": remaining_time,
            "code": state_str,
            "type": self._get_traffic_light_type_name(logic.type),
            "lanes": lanes_info,
            "phases": logics_serialized
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
    
    def get_total_vehicle_count(self):
        return sum(self.get_vehicle_counts_by_lane().values())

    def get_total_pedestrian_count(self):
        return sum(self.get_pedestrian_counts_by_lane().values())

    