import traci

class Vehicle:
    def __init__(self, vehID, routeID):
        """
        :param vehID: identifiant du véhicule
        :param routeID: identifiant de la route
        """
        self.vehID = vehID
        self.routeID = routeID
        self.typeID = "car"

        # Paramètres de départ/arrivée
        self.depart = 0.0           # début de l'edge
        self.departLane = "best"
        self.departPos = 0.0        # départ au début de l'edge
        self.departSpeed = "max"
        self.arrivalLane = "current"
        self.arrivalPos = 0.0       # position valide pour SUMO ("random", "max" ou float)
        self.arrivalSpeed = 0.0

        # Paramètres pour éviter blocage au carrefour
        self.minGap = 2.0           # distance minimum avec véhicule devant
        self.accel = 3.0            # accélération
        self.decel = 8.0            # décélération
        self.laneChangeMode = 0b111111111  # autorise tous les changements de voie
        self.tau = 0.5              # temps de réaction (plus réactif)

    def create_vehicle(self):
        """
        Crée la route si nécessaire, puis le véhicule dans SUMO.
        """
        import traci

        # Créer la route si elle n'existe pas
        if self.routeID not in traci.route.getIDList():
            route_edges_map = {
                "E2W": ["E2C", "C2W"],
                "N2S": ["N2C", "C2S"],
                "S2N": ["S2C", "C2N"],
                "W2E": ["W2C", "C2E"]
            }
            edges = route_edges_map.get(self.routeID, [])
            if edges:
                traci.route.add(self.routeID, edges)

        # Créer le véhicule
        traci.vehicle.add(
            vehID=self.vehID,
            routeID=self.routeID,
            typeID=self.typeID,
            depart=self.depart,
            departLane=self.departLane,
            departPos=self.departPos,
            departSpeed=self.departSpeed,
            arrivalLane=self.arrivalLane,
            arrivalPos=self.arrivalPos,  # float ou "max" ou "random"
            arrivalSpeed=self.arrivalSpeed,
        )

        # Configurer les paramètres dynamiques pour éviter blocage
        traci.vehicle.setMinGap(self.vehID, self.minGap)
        traci.vehicle.setAccel(self.vehID, self.accel)
        traci.vehicle.setDecel(self.vehID, self.decel)
        traci.vehicle.setLaneChangeMode(self.vehID, self.laneChangeMode)
        traci.vehicle.setTau(self.vehID, self.tau)

