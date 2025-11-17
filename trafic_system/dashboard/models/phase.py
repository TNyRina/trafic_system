import traci

class Phase:
    def __init__(self, tl_id):
        self.tl_id = tl_id
        self._phase = traci.trafficlight.getPhase(tl_id)
        self._controlled_lanes = traci.trafficlight.getControlledLanes(self.tl_id)

    def getPhase(self): 
        return self._phase
    
    def logics_serialized(self):
        """
        Sérialise les logics du feu avec les phases et le signal par direction.
        Ajout : regroupement des phases par état global (G/Y/R) + durée.
        """
        logics = traci.trafficlight.getCompleteRedYellowGreenDefinition(self.tl_id)

        logics_serialized = []

        for logic in logics:
            
            # Normaliser structure SUMO
            if hasattr(logic, "programID"):
                programID = logic.programID
                tl_type = logic.type
                currentPhaseIndex = getattr(logic, "currentPhaseIndex", None)
                phases = logic.phases
            else:
                programID = logic[0] if len(logic) > 0 else None
                tl_type = logic[1] if len(logic) > 1 else None
                currentPhaseIndex = logic[2] if len(logic) > 2 else None
                phases = logic[3] if len(logic) > 3 else []

            logic_dict = {
                "programID": programID,
                "currentPhaseIndex": currentPhaseIndex,
                "phases": []
            }

            logics_serialized.append(self._regroup_phases_by_state(phases, logic_dict))

        return logics_serialized
    
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

    def _regroup_phases_by_state(self, phases, logic_dict):
        """
        Regroupe les phases par état global G/Y/R pour véhicules.
        Les phases vertes sont séparées en 'main' (longues) et 'short' (transitions) 
        selon un mapping fixe par index pour éviter que changer la durée modifie le groupe.
        """
        # --- Configuration des phases vertes fixes ---
        # Ici tu définis les index connus de green.main et green.short
        green_main_indexes = [0, 3]  # remplacer par les index réels de vos verts longs
        green_short_indexes = [1, 4]  # remplacer par les index réels des verts courts

        grouped_by_state = {
            "green": {"main": [], "short": []},
            "yellow": [],
            "red": [],
        }

        for i, phase in enumerate(phases):

            # Normaliser phase
            if hasattr(phase, "duration"):
                duration = phase.duration
                state = phase.state
                minDur = getattr(phase, "minDur", None)
                maxDur = getattr(phase, "maxDur", None)
            else:
                duration = phase[0] if len(phase) > 0 else None
                state = phase[1] if len(phase) > 1 else ""
                minDur = phase[2] if len(phase) > 2 else None
                maxDur = phase[3] if len(phase) > 3 else None

            # Signaux véhicules / piétons
            vehicle_directions = {"N": [], "S": [], "E": [], "W": []}
            pedestrian_lanes = {}

            for lane, sig in zip(self._controlled_lanes, state):
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

            # Consolidation G/Y/R pour véhicules
            global_signals = {}
            for dirc, sigs in vehicle_directions.items():
                if signals := sigs:
                    if all(s in ["g", "G"] for s in signals):
                        global_signals[dirc] = "g"
                    elif any(s == "y" for s in signals):
                        global_signals[dirc] = "y"
                    elif all(s == "r" for s in signals):
                        global_signals[dirc] = "r"
                    else:
                        global_signals[dirc] = "mixed"
                else:
                    global_signals[dirc] = "r"

            vehicle_state_str = "".join(global_signals.values())

            # Déterminer le groupe global
            if "y" in vehicle_state_str:
                grouped_by_state["yellow"].append({
                    "index": i,
                    "duration": duration,
                    "state": state,
                    "signals": global_signals,
                    "pedestrian_signals": pedestrian_lanes,
                })
            elif all(c == "r" for c in vehicle_state_str):
                grouped_by_state["red"].append({
                    "index": i,
                    "duration": duration,
                    "state": state,
                    "signals": global_signals,
                    "pedestrian_signals": pedestrian_lanes,
                })
            else:
                # Vert → utiliser mapping fixe par index
                if i in green_main_indexes:
                    subgroup = "main"
                elif i in green_short_indexes:
                    subgroup = "short"
                else:
                    subgroup = "short"  # par défaut si non spécifié
                grouped_by_state["green"][subgroup].append({
                    "index": i,
                    "duration": duration,
                    "state": state,
                    "signals": global_signals,
                    "pedestrian_signals": pedestrian_lanes,
                })

        logic_dict["grouped_by_state"] = grouped_by_state
        return logic_dict

    
    def set_phase_duration_by_group_yellow(self, new_duration):

        self.set_phase_duration_by_group("yellow", new_duration)
    
    def set_phase_duration_by_group_green_main(self, new_duration):
        self.set_phase_duration_by_group("green.main", new_duration)
    
    def set_phase_duration_by_group_green_short(self,new_duration):
        self.set_phase_duration_by_group( "green.short", new_duration)

    def set_phase_duration_by_group(self, group_name: str, new_duration: float):
        """
        Change la durée de toutes les phases d'un groupe ('green.main', 'green.short', 'yellow', etc.)

        :param group_name: nom du groupe à modifier
        :param new_duration: nouvelle durée en secondes
        """
        try:
            # Sérialisation des phases avec regroupement
            logic_dict = self.logics_serialized()[0]
            grouped = logic_dict.get("grouped_by_state", {})

            # Récupérer les phases à modifier
            if '.' in group_name:
                main_group, sub_group = group_name.split('.')
                phases_to_modify = grouped.get(main_group, {}).get(sub_group, [])
            else:
                phases_to_modify = grouped.get(group_name, [])

            if not phases_to_modify:
                print(f"⚠️ Aucun phase trouvé pour le groupe '{group_name}'")
                return False

            # Récupération du programme complet
            logics = traci.trafficlight.getCompleteRedYellowGreenDefinition(self.tl_id)
            logic = logics[0]

            # Copie des phases
            phases = list(logic.phases)

            # Modification des phases du groupe
            for phase_info in phases_to_modify:
                idx = phase_info["index"]
                old_phase = phases[idx]
                phases[idx] = traci.trafficlight.Phase(
                    duration=new_duration,
                    state=old_phase.state,
                    minDur=new_duration,
                    maxDur=new_duration
                )

            # Création de la nouvelle logique avec les phases modifiées
            new_logic = traci.trafficlight.Logic(
                logic.programID,
                logic.type,
                logic.currentPhaseIndex,
                phases
            )

            # Application et rechargement du programme
            traci.trafficlight.setCompleteRedYellowGreenDefinition(self.tl_id, new_logic)
            traci.trafficlight.setProgram(self._id, new_logic.programID)

            print(f"✅ Durée des phases du groupe '{group_name}' modifiée à {new_duration}s")
            return True

        except traci.exceptions.TraCIException as e:
            print("Erreur TraCI :", e)
            return False
        except Exception as e:
            print("Erreur :", e)
            return False

