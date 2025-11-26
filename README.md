# trafic_system

## Installation  
1. Installer SUMO   
Aller sur le site officel de SUMO : https://eclipse.dev/sumo/
3. Cloner le projet  
- git clone https://github.com/TNyRina/trafic_system.git  

3. Creer un envirenement virtuel dans le dossier trafic_system   
- python -m venv venv_name  
- source venv_name/bin/activate  

4. Installer les dépendances  
- pip install -r requirements.txt  

## Tester si SUMO fonctionne 
python test_sumo_terminal.py

## API
Aller dans le dossier 'trafic_system' qui contient le fichier manage.py, et lancer la commander $ python manage.py runserver  
Ouvrir le lien http://127.0.0.1:8000/dashboard/ 

|lien                                   | API
|---------------------------------------|-----------------------
|'/'                                    | dashboard static
|'/start'                               | demarer la simulation
|'/data'                                | dasboard dynamique (demarer la simulation avant de recuperer les informations dynamiques) 
|'/traffic_light/stop_all'              | bloquer toutes les voies
|'/traffic_light/restore_controle'      | restaurer l'etat du feu tricolor
|'traffic_light/prioritize/<int:lane>/  | prioriser une voie par son id
|'traffic_light/prioritize_direction/<str:direction>/  | prioriser une voie par direction (N/S/E/W)
|'traffic_light/change_phase/yellow/<int:duration>/'   | changer la duration de la phase jaune
|'traffic_light/change_phase/green_main/<int:duration>/' | changer la duration de la phase verte longue (passage pieton non bloquer)
|'traffic_light/change_phase/green_short/<int:duration>/' | changer la duration de la phase verte courte (passage pieton bloquer)
|'/stop' | Stop la simulation et sauvegrade le statistique 
|'/statistics' | Liste les statistics
|'statistic/delete/<int: id_stat>' | suprime un stastique
|'/statistic/filter/date/?start_date=2025-11-20&end_date=2025-11-23'    |
|'/statistic/filter/date/?start_date=2025-11-20'                        | filtre static par date    
|'/statistic/filter/date/''                                             |    


**Important** : actualiser la page pour voir le changement des donnees dynamiques
