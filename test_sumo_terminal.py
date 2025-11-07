import traci

CONFIG_FILE = "carrefour4_netgenerate/carrefour.sumocfg"

# Lancer SUMO
sumo_cmd = ["sumo", "-c", CONFIG_FILE]
traci.start(sumo_cmd)

try:
    # Sélection du feu principal
    tl_id = traci.trafficlight.getIDList()[0]

    # Récupérer la définition complète du feu
    logic = traci.trafficlight.getCompleteRedYellowGreenDefinition(tl_id)[0]

    # Cycle total = somme des durées de toutes les phases
    total_cycle_duration = sum(phase.duration for phase in logic.phases)

    print(f"Feu de circulation : {tl_id}")
    print(f"Programme : {logic.programID}, Type : {logic.type}, Cycle total : {total_cycle_duration}s")
    print(f"Nombre de phases : {len(logic.phases)}\n")

    # Parcourir toutes les phases
    for i, phase in enumerate(logic.phases):
        print(f"Phase {i + 1}:")
        print(f"  Nom : {phase.name}")
        print(f"  Etat brut : {phase.state}")
        print(f"  Durée : {phase.duration}s")

        # Lanes et signaux
        controlled_lanes = traci.trafficlight.getControlledLanes(tl_id)
        print("  Lanes contrôlées et signaux pour cette phase :")
        for lane, sig in zip(controlled_lanes, phase.state):
            print(f"    {lane} -> {sig}")
        print("\n")

finally:
    traci.close()
    print("Simulation fermée.")