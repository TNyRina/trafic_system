import traci

CONFIG_FILE = "carrefour4_netgenerate/carrefour.sumocfg"

# Démarre SUMO (mode non graphique)
sumo_cmd = ["sumo", "-c", CONFIG_FILE]

traci.start(sumo_cmd)

print("Liste des edges :", traci.edge.getIDList())
print("Liste des lanes :", traci.lane.getIDList())
print("Liste des feux :", traci.trafficlight.getIDList())
traci.close()
