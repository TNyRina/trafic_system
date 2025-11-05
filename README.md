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

## Ouvrir le dashboard (interface web)
Aller dans le dossier 'trafic_system' qui contient le fichier manage.py, et lancer la commander $ python manage.py runserver  
Ouvrir le lien http://127.0.0.1:8000/dashboard/
