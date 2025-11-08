import traci

CONFIG_FILE = "carrefour4_netgenerate/carrefour.sumocfg"

# Lancer SUMO
sumo_cmd = ["sumo", "-c", CONFIG_FILE]
traci.start(sumo_cmd)

try:
    route_ids = traci.route.getIDList()
    # print(route_ids)
    for route in route_ids:
        print("\nroute " + route)
        print("edges:")
        for e in traci.route.getEdges(route):
            print(e, traci.lane.getLength(e + "_0"))


finally:
    traci.close()
    print("Simulation fermée.")