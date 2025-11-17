import traci
from .phase import Phase    
class TrafficLight :
    def __init__(self):
        self._id = traci.trafficlight.getIDList()[0]

        self.phase = Phase(self._id)
        
        self._controlled_lanes = traci.trafficlight.getControlledLanes(self._id)
        # normaliser la récupération du premier logic (accepte tuple ou objet)
        logics = traci.trafficlight.getCompleteRedYellowGreenDefinition(self._id)
        self._logic = logics[0] if logics else None
        self._phase = traci.trafficlight.getPhase(self._id)

        self._meanings_singal = {
            "r": "Rouge (interdiction totale)",
            "y": "Jaune (transition)",
            "g": "Vert (autorisation partielle)",
            "G": "Vert (prioritaire)",
            "s": "Stop/Clignotement",
            "O": "Aucun signal",
            "p": "Piétons : passage autorisé",
            "P": "Piétons : arrêt obligatoire",
        }




    #=========================
    # TL state
    #========================
    
    def get_state(self):
        return traci.trafficlight.getRedYellowGreenState(self._id)

    def set_state(self, state):
        try:
            traci.trafficlight.setRedYellowGreenState(self._id, state)
        except traci.exceptions.TraCIException as e:
            print("Erreur TraCI :", e)






    #============================
    # TL controle
    #============================
    def restore_controle(self):
        try:
            traci.trafficlight.setProgram(self._id, 0)
        except traci.exceptions.TraCIException as e:
            print("Erreur TraCI :", e)
    
    def prioritize_lane(self, lane_index):
        new_state = self._build_state_by_lane_index(lane_index)

        try:
            traci.trafficlight.setRedYellowGreenState(self._id, "".join(new_state))
        except traci.exceptions.TraCIException as e:
            print("Erreur TraCI :", e)

    def prioritize_lane_by_direction(self, directions):
        """
        Priorise une ou plusieurs directions et bloque toutes les autres.
        :param directions: chaîne de caractères représentant les directions à prioriser
                        ex: "N", "S", "NS", "WE"
        """
        new_state = self._build_state_by_direction(directions)
        
        new_state_str = ''.join(new_state)

        try:
            traci.trafficlight.setRedYellowGreenState(self._id, new_state_str)
        except traci.exceptions.TraCIException as e:
            print("Erreur TraCI :", e) 





    #============================
    # Infos
    #=============================

    def get_info(self):
        """
        État complet du feu principal avec infos dynamiques pour chaque lane.
        """
        current_time = traci.simulation.getTime()
        next_switch = traci.trafficlight.getNextSwitch(self._id)
        remaining_time = next_switch - current_time

        phases = self._logic.getPhases()
        current_phase = phases[self.phase.getPhase()]
    
        return {
            "id": self._id,
            "phase": self.phase.getPhase(),
            "duration": current_phase.duration,
            "remaining_time": remaining_time,
            "state": self.get_state(),
            "state_by_direction": self._get_signals_by_direction(),
            "type": self._get_type_name(self._logic.type),
            "lanes": self._get_lanes_info(),
            "phases": self.phase.logics_serialized()
        }


    def _get_signals_by_direction(self):
        """
        Regroupe les signaux d’un feu tricolore par direction (N, S, E, W, pedestrians).
        :param tl_id: ID du feu de circulation
        :return: dict regroupant les états des feux par direction
        """
        state = self.get_state()
        controlled_lanes = self._controlled_lanes

        vehicle_directions = {"N": [], "S": [], "E": [], "W": []}
        pedestrian_signals = []

        for lane, signal in zip(controlled_lanes, state):
            lane_lower = lane.lower()
            if "ped" in lane_lower or lane.startswith(":"):
                pedestrian_signals.append(signal)
            elif "n" in lane_lower:
                vehicle_directions["N"].append(signal)
            elif "s" in lane_lower:
                vehicle_directions["S"].append(signal)
            elif "e" in lane_lower:
                vehicle_directions["E"].append(signal)
            elif "w" in lane_lower:
                vehicle_directions["W"].append(signal)

        aggregated_signals = {dir: self._aggregate(sigs) for dir, sigs in vehicle_directions.items()}

        return {
            "vehicles": aggregated_signals,
            "pedestrians": pedestrian_signals
        }


    def _aggregate(self, sig_list):
        if any(s.lower() == 'g' for s in sig_list):
            return 'g'
        elif any(s.lower() == 'y' for s in sig_list):
            return 'y'
        else:
            return 'r'



    #=================================
    # private method
    #=================================
    def _build_state_by_lane_index(self, index):
        state = list(self.get_state())
        new_state = []
        for i in range(len(state)):
            if i == index:
                new_state.append("G")
            else:
                if self._controlled_lanes[i].startswith(":"):
                    new_state.append("r")  
                else:
                    new_state.append("r")  
        
        return new_state
    

    def _get_lane_indexes_by_direction(self, direction):
        
        lane_indexes = []
        for i, lane in enumerate(self._controlled_lanes):
            if lane.upper().startswith(direction):
                lane_indexes.append(i)
        
        return lane_indexes

    def _build_state_by_direction(self, directions):
        priority_indexes = self._priority_index_for_directions(directions)

        new_state = []
        for i, lane in enumerate(self._controlled_lanes):
            if i in priority_indexes:
                if 'ped' in lane.lower() or lane.startswith(':'):
                    new_state.append('p')  
                else:
                    new_state.append('G') 
            else:
                new_state.append('r')
        
        return new_state

    def _priority_index_for_directions(self, directions):
        priority_indexes = []
        for dir_char in directions.upper():
            priority_indexes.extend(self._get_lane_indexes_by_direction(dir_char))

        return priority_indexes


    def _get_lanes_info(self):
        lanes_info = {}

        for i,(lane, sig) in enumerate(zip(self._controlled_lanes, self.get_state())):
            lname = lane.lower()
            type_voie = self._get_lane_type(lname)
            direction = self._get_lane_direction(lname, type_voie)

            lanes_info[lane] = {
                "id": lane,
                "index": i,
                "type": type_voie,
                "direction": direction,
                "signal": sig,
                "meaning": self._meanings_singal.get(sig, f"Inconnu ({sig})"),
                "num_vehicles": traci.lane.getLastStepVehicleNumber(lane),
                "vehicle_ids": traci.lane.getLastStepVehicleIDs(lane),
                "occupancy": traci.lane.getLastStepOccupancy(lane),
                "mean_speed": traci.lane.getLastStepMeanSpeed(lane),
                "waiting_time": traci.lane.getWaitingTime(lane)
            }

        return lanes_info

    def _get_lane_type(self, name):
        if "_w" in name or "ped" in name:
            return "pieton"
        return "voiture"

    def _get_lane_direction(self, name, type):
        direction = "inconnue"

        if "n2" in name or name.startswith("n_"):
                direction = "nord"
        elif "s2" in name or name.startswith("s_"):
            direction = "sud"
        elif "e2" in name or name.startswith("e_"):
            direction = "est"
        elif "w2" in name or name.startswith("w_"):
            direction = "ouest"

        if type == "pieton":
            if "n_w" in name or "n2s" in name or "n2s_w" in name:
                direction = "nord_sud"
            elif "s_w" in name or "s2n" in name or "s2n_w" in name:
                direction = "sud_nord"
            elif "e_w" in name or "e2w" in name or "e2w_w" in name:
                direction = "est_ouest"
            elif "w_e" in name or "w2e" in name or "w2e_w" in name:
                direction = "ouest_est"
        
        return direction
    
    def _get_type_name(self, tl_type):
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