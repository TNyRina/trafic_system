from trafic_system.simulation.traci_client import SumoController
import time

CONFIG_FILE = "carrefour4/simulation.sumocfg"

controller = SumoController(CONFIG_FILE, gui=True)

traffic_light_id = "c"

try:
    for step in range(100):
        controller.step()

        time.sleep(0.1)

finally:
    controller.close()
