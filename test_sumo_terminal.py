import traci
import sys
import time

# Nom de ton fichier de configuration SUMO
SUMO_CFG = "carrefour4_netgenerate/carrefour.sumocfg"

def main():
    try:
        # --- Démarrage de SUMO en mode non graphique (mets "sumo-gui" si tu veux voir visuellement) ---
        traci.start(["sumo", "-c", SUMO_CFG])

        # Récupération de l'ID du premier feu tricolore
        tls_id = traci.trafficlight.getIDList()[0]
        print(f"Feu tricolore sélectionné : {tls_id}")

    
        print("type : \n")
        logic = traci.trafficlight.getCompleteRedYellowGreenDefinition(tls_id)[0]
        print(logic)
        logic.type = 50

        print("Apres changement de type : \n")
        print(logic)
        

    except Exception as e:
        print("Erreur :", e)
    finally:
        traci.close()

if __name__ == "__main__":
    main()
