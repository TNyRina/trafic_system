import traci

class TrafficLight :
    def __init__(self):
        self._id = traci.trafficlight.getIDList()[0]
        
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
        current_phase = phases[self._phase]
    
        return {
            "id": self._id,
            "phase": self._phase,
            "duration": current_phase.duration,
            "remaining_time": remaining_time,
            "state": self.get_state(),
            "state_by_direction": self._get_signals_by_direction(),
            "type": self._get_type_name(self._logic.type),
            "lanes": self._get_lanes_info(),
            "phases": self._logics_serialized()
        }



    #==================================
    # Phases
    #===================================

    def set_phase_duration(self, index_phase: int, new_duration: float):
        """
        Change la durée d'une phase spécifique d'un feu de circulation.

        :param phase_index: index de la phase à modifier (0-based)
        :param new_duration: nouvelle durée en secondes
        """

        try:

            # Récupération du programme complet du feu
            logics = traci.trafficlight.getCompleteRedYellowGreenDefinition(self._id)
            logic = logics[0]

            # Vérifie si l'index est valide
            if index_phase >= len(logic.phases):
                print(f"❌ Index {index_phase} invalide (max {len(logic.phases)-1})")
                traci.close()
                return

            # Copie des phases et modification
            phases = list(logic.phases)
            phase_modifiee = phases[index_phase]
            phases[index_phase] = traci.trafficlight.Phase(
                duration=new_duration,
                state=phase_modifiee.state,
                minDur=getattr(phase_modifiee, "minDur", 0),
                maxDur=getattr(phase_modifiee, "maxDur", 0)
            )

            # Création de la nouvelle logique avec la phase modifiée
            new_logic = traci.trafficlight.Logic(
                logic.programID, logic.type, logic.currentPhaseIndex, phases
            )

            # Application et rechargement du programme
            traci.trafficlight.setCompleteRedYellowGreenDefinition(self._id, new_logic)
            traci.trafficlight.setProgram(self._id, new_logic.programID)

        except traci.exceptions.TraCIException as e:
            print("Erreur TraCI :", e)
            return False
        except Exception as e:
            print("Erreur :", e)
            return False





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
    
    

    def _logics_serialized(self):
        """
        Sérialise les logics du feu avec les phases et le signal par direction.
        Supporte les objets traci *et* les tuples (compatibilité versions).
        """
        logics = traci.trafficlight.getCompleteRedYellowGreenDefinition(self._id)
        controlled_lanes = traci.trafficlight.getControlledLanes(self._id)

        logics_serialized = []

        for logic in logics:
            # normaliser fields (objet ou tuple)
            if hasattr(logic, "programID"):
                programID = logic.programID
                tl_type = logic.type
                currentPhaseIndex = getattr(logic, "currentPhaseIndex", None)
                phases = logic.phases
            else:
                # tuple-like: (programID, type, currentPhaseIndex, phases)
                programID = logic[0] if len(logic) > 0 else None
                tl_type = logic[1] if len(logic) > 1 else None
                currentPhaseIndex = logic[2] if len(logic) > 2 else None
                phases = logic[3] if len(logic) > 3 else []

            logic_dict = {
                "programID": programID,
                "type": self._get_type_name(tl_type),
                "currentPhaseIndex": currentPhaseIndex,
                "phases": []
            }

            for phase in phases:
                # normaliser phase (objet ou tuple)
                if hasattr(phase, "duration"):
                    duration = phase.duration
                    state = phase.state
                    minDur = getattr(phase, "minDur", None)
                    maxDur = getattr(phase, "maxDur", None)
                else:
                    # tuple-like: (duration, state, minDur, maxDur, ...)
                    duration = phase[0] if len(phase) > 0 else None
                    state = phase[1] if len(phase) > 1 else ""
                    minDur = phase[2] if len(phase) > 2 else None
                    maxDur = phase[3] if len(phase) > 3 else None

                # Calcul des signaux par direction
                vehicle_directions = {"N": [], "S": [], "E": [], "W": []}
                pedestrian_lanes = {}

                for lane, sig in zip(controlled_lanes, state):
                    lane_lower = lane.lower()
                    if "ped" in lane_lower or lane.startswith(":"):
                        pedestrian_lanes[lane] = sig
                    elif "n" in lane_lower:
                        vehicle_directions["N"].append(sig)
                    elif "s" in lane_lower:
                        vehicle_directions["S"].append(sig)
                    elif "e" in lane_lower:
                        vehicle_directions["E"].append(sig)
                    elif "w" in lane_lower:
                        vehicle_directions["W"].append(sig)

                global_signals = {}
                for dirc, signals in vehicle_directions.items():
                    if signals and all(s in ["g", "G"] for s in signals):
                        global_signals[dirc] = "g"
                    elif signals and all(s == "r" for s in signals):
                        global_signals[dirc] = "r"
                    elif any(s == "y" for s in signals):
                        global_signals[dirc] = "y"
                    else:
                        global_signals[dirc] = "r"

                logic_dict["phases"].append({
                    "duration": duration,
                    "state": state,
                    "minDur": minDur,
                    "maxDur": maxDur,
                    "vehicle_signals": global_signals,
                    "pedestrian_signals": pedestrian_lanes
                })

            logics_serialized.append(logic_dict)

        return logics_serialized

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