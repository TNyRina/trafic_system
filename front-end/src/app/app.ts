import { Component, signal, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common'; 
import { FormsModule } from '@angular/forms'; 
import { SimulationService, PhaseConfiguration, PhaseUpdateResponse } from './simulation-service';
import { Observable, interval, Subscription } from 'rxjs';

type TrafficMode = 'auto' | 'manual' | 'smart' ;
type Direction = 'NORD' | 'SUD' | 'EST' | 'OUEST';
type LightState = 'red' | 'yellow' | 'green';

interface Entity {
  id: number;
  type: 'vehicule' | 'piéton';
  direction: Direction;
  label?: string;
}

interface TrafficLightLane {
  id: string;
  index: number;
  type: 'voiture' | 'pieton';
  direction: string;
  signal: string;
  meaning: string;
  num_vehicles: number;
  vehicle_ids: string[];
  occupancy: number;
  mean_speed: number;
  waiting_time: number;
}


@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit, OnDestroy {
  protected readonly title = signal('Système de Gestion de Feux Tricolores');
  message = '';
  
  constructor(private simulationService: SimulationService) {}
  
  private refreshInterval?: Subscription;
  
  // Données du backend SUMO
  carrefour: any;
  traffic_light: any;
  tl_lanes: TrafficLightLane[] = [];
  
  // États de l'application
  modes: TrafficMode[] = ['auto', 'manual', 'smart', ];
  mode: TrafficMode = 'auto';
  simulationRunning = false;
  isLoading = false;

  // Configuration des durées
  greenDuration = 30;
  yellowDuration = 5;
  redDuration = 30;

  // Directions
  directions: Direction[] = ['NORD', 'SUD', 'EST', 'OUEST'];
  priorityDirection: Direction | null = null;

  // UX et messages
  lastActionMessage = '';

  // Statistiques en temps réel
  stats = {
    totalVehicles: 0,
    totalPedestrians: 0,
    totalWaitingTime: 0,
    averageSpeed: 0
  };

  // Entités (optionnel)
  entities: Entity[] = [];
  nextEntityId = 1;
  newEntity: Partial<Entity> = { type: 'vehicule', direction: 'NORD' };

  // Dans app.ts - Remplacez par vos index réels
private laneIndexes = {
  'NORD': { 
    straight: [1, 2],    // Deux index pour Nord tout droit
    right: [0]           // Un index pour Nord droite (si existe)
  },
  'SUD': { 
    straight: [11, 12],    // Deux index pour Sud tout droit  
    right: [10]           // Un index pour Sud droite (si existe)
  },
  'EST': { 
    straight: [6, 7],    // Deux index pour Est tout droit
    right: [5]           // Un index pour Est droite (si existe)
  },
  'OUEST': { 
    straight: [16, 17],  // Deux index pour Ouest tout droit
    right: [15]          // Un index pour Ouest droite (si existe)
  }
};

// Dans app.ts - Un seul index par direction piéton
private pedestrianIndexes = {
  'NORD': 20,      // Index unique pour piétons Nord
  'SUD': 22,       // Index unique pour piétons Sud  
  'EST': 21,       // Index unique pour piétons Est
  'OUEST': 23      // Index unique pour piétons Ouest
};

// === CONFIGURATION DES DURÉES DE PHASE ===
  
  // Configuration par groupe
  greenMainDuration: number = 30;
  greenShortDuration: number = 15;

  // Configuration individuelle
  individualPhaseIndex: number = 0;
  individualPhaseDuration: number = 30;

  // === MÉTHODES DE CONFIGURATION ===

  // Mettre à jour la durée des phases jaunes
  updateYellowDuration() {
    if (this.yellowDuration <= 0) {
      this.message = 'La durée jaune doit être positive';
      return;
    }

    this.isLoading = true;
    this.simulationService.changeYellowPhaseDuration(this.yellowDuration).subscribe({
      next: (response) => {
        this.message = `Durée jaune mise à jour: ${this.yellowDuration}s`;
        this.isLoading = false;
      },
      error: (error) => {
        this.message = 'Erreur lors de la mise à jour jaune';
        this.isLoading = false;
      }
    });
  }

  // Mettre à jour une phase individuelle
  updateIndividualPhase() {
    if (this.individualPhaseDuration <= 0) {
      this.message = 'La durée doit être positive';
      return;
    }

    this.isLoading = true;
    this.simulationService.changePhaseDuration(this.individualPhaseIndex, this.individualPhaseDuration).subscribe({
      next: (response) => {
        this.message = `Phase ${this.individualPhaseIndex} mise à jour: ${this.individualPhaseDuration}s`;
        this.isLoading = false;
      },
      error: (error) => {
        this.message = 'Erreur lors de la mise à jour de la phase';
        this.isLoading = false;
      }
    });
  }

  // Arrêter tous les feux
  stopAllTrafficLights() {
    this.isLoading = true;
    this.simulationService.stopAllTl().subscribe({
      next: (response) => {
        this.message = 'Tous les feux sont arrêtés';
        this.isLoading = false;
      },
      error: (error) => {
        this.message = 'Erreur lors de l\'arrêt des feux';
        this.isLoading = false;
      }
    });
  }

  // Rétablir le contrôle automatique
  restoreControl() {
    this.isLoading = true;
    this.simulationService.restoreControleTl().subscribe({
      next: (response) => {
        this.message = 'Contrôle automatique rétabli';
        this.isLoading = false;
      },
      error: (error) => {
        this.message = 'Erreur lors du rétablissement du contrôle';
        this.isLoading = false;
      }
    });
  }


  phaseConfigurations: PhaseConfiguration[] = [];
  selectedPhase: PhaseConfiguration | null = null;
  newDuration: number = 0;

  // Configuration des groupes de phases
    groupDurations = {
    red: 0,
    yellow: 0,
    green: 0
  };


  

  // Sélectionner une phase pour modification
  selectPhase(phase: PhaseConfiguration) {
    this.selectedPhase = phase;
    this.newDuration = phase.duration;
  }


  // Annuler la modification
  cancelEdit() {
    this.selectedPhase = null;
    this.newDuration = 0;
    this.message = '';
  }

  ngOnInit(): void {
    this.loadCarrefourData();
  }

  ngOnDestroy(): void {
    this.stopDynamicDataRefresh();
  }

  // ------------ CHARGEMENT ET SYNCHRONISATION DES DONNÉES ---------------
  private loadCarrefourData(): void {
    this.isLoading = true;
    this.simulationService.getStaticCarrefourData().subscribe({
      next: (data) => {
        this.processSumoData(data);
        console.log('✅ Données SUMO chargées :', data);
        this.isLoading = false;
      },
      error: (err) => this.handleError('Erreur lors du chargement des données SUMO', err),
    });
  }

  // private startDynamicDataRefresh(): void {
  //   this.stopDynamicDataRefresh();
  //   this.refreshInterval = interval(1000).subscribe(() => {
  //     this.simulationService.getDynamicCarrefourData().subscribe({
  //       next: (data) => {
  //         if (data.sumo === 'inactive') {
  //           this.stopDynamicDataRefresh();
  //           this.simulationRunning = false;
  //           return;
  //         }
  //         this.processSumoData(data);
  //       },
  //       error: (err) => this.handleError('Erreur lors de la mise à jour dynamique', err),
  //     });
  //   });
  // }

  private stopDynamicDataRefresh(): void {
    if (this.refreshInterval) {
      this.refreshInterval.unsubscribe();
      this.refreshInterval = undefined;
    }
  }

  private processSumoData(data: any): void {
    this.carrefour = data;
    this.traffic_light = data.traffic_light_info;
    this.tl_lanes = Object.values(data.traffic_light_info?.lanes || []);
    this.updateStatistics();
    this.initializeDurationsFromSumo();
    
    const pedestrianLanes = this.tl_lanes.filter(lane => lane.type === 'pieton');
  // console.log('🔄 PIÉTONS - Voies trouvées:', pedestrianLanes.length);
  
 
  }

  // ------------ GESTION DES DURÉES ---------------
  private initializeDurationsFromSumo() {
    if (this.traffic_light?.phases?.[0]) {
      const currentPhase = this.traffic_light.phases[this.traffic_light.phase];
      if (currentPhase) {
        this.greenDuration = currentPhase.duration || 30;
      }
    }
  }

  updateDurations() {
    this.flash(`⏱️ Durées mises à jour: Vert=${this.greenDuration}s, Jaune=${this.yellowDuration}s, Rouge=${this.redDuration}s`);
    
    // TODO: Implémenter l'envoi des nouvelles durées à SUMO
    console.log('Nouvelles durées à envoyer à SUMO:', {
      green: this.greenDuration,
      yellow: this.yellowDuration,
      red: this.redDuration
    });
  }

  // ------------ GESTION SIMULATION ---------------
  startSimulation() {
    this.isLoading = true;
    this.updateMessage('Démarrage de la simulation SUMO...');

    this.simulationService.startSimulation().subscribe({
      next: (response) => {
        this.updateMessage('✅ Simulation SUMO démarrée avec succès !');
        this.simulationRunning = true;
        this.startDynamicDataRefresh();
        this.isLoading = false;
      },
      error: (err) => {
        this.handleError('❌ Erreur lors du démarrage de la simulation SUMO', err);
        this.isLoading = false;
      },
    });
  }

  stopSimulation() {
    this.simulationRunning = false;
    this.stopDynamicDataRefresh();
    this.flash('Simulation SUMO arrêtée');
    this.updateMessage('Simulation SUMO arrêtée');
  }

  // ------------ SYNCHRONISATION DES FEUX AVEC SUMO ---------------
  getLightStateFromSumo(direction: Direction): LightState {
    if (!this.traffic_light?.state_by_direction?.vehicles) {
      console.warn('❌ Données SUMO manquantes pour les feux');
      return 'red';
    }

    // Conversion des directions vers le format SUMO
    const sumoDirection = this.getSumoDirection(direction);
    const sumoState = this.traffic_light.state_by_direction.vehicles[sumoDirection];
    
    // Conversion des états SUMO vers nos états d'interface
    switch (sumoState) {
      case 'G': // Vert prioritaire SUMO
      case 'g': // Vert autorisation partielle SUMO
        return 'green';
      case 'y': // Jaune SUMO
      case 'Y': // Jaune clignotant SUMO
        return 'yellow';
      case 'r': // Rouge SUMO
      case 'R': // Rouge strict SUMO
        return 'red';
      default:
        console.warn(`❌ État SUMO inconnu: ${sumoState} for ${direction}`);
        return 'red';
    }
  }

  // Méthode pour convertir nos directions vers le format SUMO
  private getSumoDirection(direction: Direction): string {
    const directionMap: Record<Direction, string> = {
      'NORD': 'N',
      'SUD': 'S', 
      'EST': 'E',
      'OUEST': 'W'
    };
    return directionMap[direction] || direction.charAt(0);
  }

  // Méthode de debug pour afficher les données SUMO
  debugSumoState(): void {
    console.log('🐛 DEBUG SUMO COMPLET:', {
      traffic_light: this.traffic_light,
      state_by_direction: this.traffic_light?.state_by_direction,
      vehicles: this.traffic_light?.state_by_direction?.vehicles,
      current_phase: this.traffic_light?.phase,
      state_string: this.traffic_light?.state
    });
    
  }

  getLightStateText(direction: Direction): string {
    const state = this.getLightStateFromSumo(direction);
    return state.toUpperCase();
  }

  getSignalMeaning(signal: string): string {
    switch (signal) {
      case 'G': return 'Vert (prioritaire)';
      case 'g': return 'Vert (autorisation partielle)';
      case 'y': return 'Jaune (attention)';
      case 'r': return 'Rouge (interdiction)';
      default: return 'Inconnu';
    }
  }

  // ------------ CONTRÔLES MANUELS ---------------
  

  applyPriority(direction: Direction) {
    this.prioritizeDirection(direction.toLowerCase());
  }


setPriorityDirection(dir: string) {
  if (!dir) {
    this.priorityDirection = null;
    this.flash('Priorité annulée');
    return;
  }
  this.priorityDirection = dir as Direction;
  
}

  // ------------ MODES ---------------
  toggleMode(m: TrafficMode) {
    this.mode = m;
    this.flash(`🔄 Mode activé : ${m}`);
    
  }

  // ------------ GESTION DES VOIES ---------------
  getLanesByDirection(direction: string): TrafficLightLane[] {
    return this.tl_lanes.filter(lane => 
      lane.direction.toLowerCase() === direction.toLowerCase() && lane.type === 'voiture'
    );
  }

  getPedestrianLanes(): TrafficLightLane[] {
    return this.tl_lanes.filter(lane => lane.type === 'pieton');
  }

  getVehicleCountForDirection(direction: string): number {
    return this.getLanesByDirection(direction).reduce((total, lane) => total + lane.num_vehicles, 0);
  }

  // ------------ STATISTIQUES ---------------
  private updateStatistics(): void {
    if (!this.tl_lanes.length) return;

    this.stats.totalVehicles = this.tl_lanes
      .filter(lane => lane.type === 'voiture')
      .reduce((sum, lane) => sum + lane.num_vehicles, 0);

    this.stats.totalPedestrians = this.tl_lanes
      .filter(lane => lane.type === 'pieton')
      .reduce((sum, lane) => sum + lane.num_vehicles, 0);

    this.stats.totalWaitingTime = this.tl_lanes
      .reduce((sum, lane) => sum + lane.waiting_time, 0);

    const speeds = this.tl_lanes.map(lane => lane.mean_speed).filter(speed => speed > 0);
    this.stats.averageSpeed = speeds.length ? 
      speeds.reduce((sum, speed) => sum + speed, 0) / speeds.length : 0;
  }

  // ------------ GESTION DES ENTITÉS ---------------
  addEntity() {
    if (!this.newEntity.type || !this.newEntity.direction) return;

    const entity: Entity = {
      id: this.nextEntityId++,
      type: this.newEntity.type as 'vehicule' | 'piéton',
      direction: this.newEntity.direction as Direction,
      label: `${this.newEntity.type} ${this.nextEntityId}`
    };

    this.entities.push(entity);
    this.flash(`${entity.type} ajouté venant du ${entity.direction}`);
    this.newEntity = { type: 'vehicule', direction: 'NORD' };
  }

  removeEntity(id: number) {
    this.entities = this.entities.filter((x) => x.id !== id);
    this.flash(`Entité ${id} supprimée`);
  }

  // ------------ UTILITAIRES ---------------
  private updateMessage(msg: string): void {
    this.message = msg;
  }

  private handleError(context: string, error: any): void {
    console.error(context, error);
    this.updateMessage(`❌ ${context}`);
    this.isLoading = false;
  }

  private flash(msg: string) {
    this.lastActionMessage = msg;
    setTimeout(() => {
      if (this.lastActionMessage === msg) this.lastActionMessage = '';
    }, 3000);
  }

  // ------------ GETTERS POUR TEMPLATE ---------------
  getNombreVehicules(): number {
    return this.entities.filter(e => e.type === 'vehicule').length;
  }

  getNombrePietons(): number {
    return this.entities.filter(e => e.type === 'piéton').length;
  }

  getRemainingTime(): number {
    return this.traffic_light?.remaining_time ?? 0;
  }

  getCurrentPhase(): number {
    return (this.traffic_light?.phase ?? 0) + 1;
  }

  getTotalLanes(): number {
    return this.tl_lanes.length;
  }

  getActiveLanes(): number {
    return this.tl_lanes.filter(lane => lane.num_vehicles > 0).length;
  }

  // Méthode pour afficher l'état brut SUMO
  getSumoRawState(direction: Direction): string {
    if (!this.traffic_light?.state_by_direction?.vehicles) return 'N/A';
    const sumoDirection = this.getSumoDirection(direction);
    const rawState = this.traffic_light.state_by_direction.vehicles[sumoDirection];
    return `SUMO: ${rawState || 'N/A'}`;
  }


  // Méthodes de test directes
  prioritizeNorth() {
    this.simulationService.prioritizeLaneByDirection('N').subscribe({
      next: () => {
        this.flash('🎯 Nord priorisé');
        this.loadCarrefourData();
      },
      error: (err) => this.handleError('Erreur Nord', err)
    });
  }

  prioritizeSouth() {
    this.simulationService.prioritizeLaneByDirection('S').subscribe({
      next: () => {
        this.flash('🎯 Sud priorisé');
        this.loadCarrefourData();
      },
      error: (err) => this.handleError('Erreur Sud', err)
    });
  }

  prioritizeEast() {
    this.simulationService.prioritizeLaneByDirection('E').subscribe({
      next: () => {
        this.flash('🎯 Est priorisé');
        this.loadCarrefourData();
      },
      error: (err) => this.handleError('Erreur Est', err)
    });
  }

  prioritizeWest() {
    this.simulationService.prioritizeLaneByDirection('W').subscribe({
      next: () => {
        this.flash('🎯 Ouest priorisé');
        this.loadCarrefourData();
      },
      error: (err) => this.handleError('Erreur Ouest', err)
    });
  }

  // ------------ MÉTHODES DE TEST DIRECTES ---------------
  prioritizeLaneByDirection(direction: string): void {
    this.simulationService.prioritizeLaneByDirection(direction).subscribe({
      next: (response) => {
        this.flash(`✅ ${this.getDirectionLabel(direction)} priorisée !`);
        console.log('Réponse backend:', response);
        
        // Recharger les données et vérifier la sync
        setTimeout(() => {
          this.loadCarrefourData();
          setTimeout(() => this.checkAllPedestrianSync(), 1000);
        }, 500);
      },
      error: (err) => this.handleError(`❌ Impossible de prioriser ${direction}`, err),
    });
  }

  // Méthode utilitaire pour les labels des directions
  private getDirectionLabel(direction: string): string {
    const labels: {[key: string]: string} = {
      'N': 'Nord',
      'S': 'Sud', 
      'E': 'Est',
      'W': 'Ouest',
      'NS': 'Nord-Sud',
      'WE': 'Ouest-Est'
    };
    return labels[direction] || direction;
  }

  // Arrêt de tous les feux (déjà existant mais amélioré)
  stopTL() {
    this.simulationService.stopTrafficLight().subscribe({
      next: (response) => {
        this.flash('🚦 Tous les feux mis en rouge');
        setTimeout(() => this.loadCarrefourData(), 500);
      },
      error: (err) => this.handleError('❌ Erreur arrêt feux', err)
    });
  }

  // Restauration du contrôle automatique (déjà existant mais amélioré)
  restoreTL() {
    this.simulationService.restoreTrafficLight().subscribe({
      next: (response) => {
        this.flash('🔄 Contrôle automatique restauré');
        setTimeout(() => this.loadCarrefourData(), 500);
      },
      error: (err) => this.handleError('❌ Erreur restauration', err)
    });
  }

  // ------------ CORRECTION DES MÉTHODES EXISTANTES ---------------

  prioritizeDirection(direction: string) {
    // Conversion des directions complètes vers format court
    const directionMap: {[key: string]: string} = {
      'nord': 'N',
      'sud': 'S',
      'est': 'E', 
      'ouest': 'W',
      'NORD': 'N',
      'SUD': 'S',
      'EST': 'E',
      'OUEST': 'W'
    };
    
    const shortDirection = directionMap[direction] || direction;
    this.prioritizeLaneByDirection(shortDirection);
  }

  // Méthodes de contrôle manuel améliorées
  // setNSGreen() {
  //   this.prioritizeLaneByDirection('NS');
  // }

  // setEWGreen() {
  //   this.prioritizeLaneByDirection('WE');
  // }

  setAllRed() {
    this.stopTL();
  }

  // Contrôle individuel des feux
  setIndividualLight(direction: Direction, state: LightState) {
    const directionMap: {[key: string]: string} = {
      'NORD': 'N',
      'SUD': 'S',
      'EST': 'E',
      'OUEST': 'W'
    };
    
    const shortDirection = directionMap[direction];
    
    // Pour l'instant, on utilise prioritize comme approximation
    // Vous pourriez étendre votre backend pour gérer les états individuels
    if (state === 'green') {
      this.prioritizeLaneByDirection(shortDirection);
    } else if (state === 'red') {
      // Pour mettre en rouge, on pourrait prioriser une direction perpendiculaire
      const perpendicularDirection = this.getPerpendicularDirection(shortDirection);
      this.prioritizeLaneByDirection(perpendicularDirection);
    }
  }

  // Méthode utilitaire pour obtenir la direction perpendiculaire
  private getPerpendicularDirection(direction: string): string {
    const perpendicularMap: {[key: string]: string} = {
      'N': 'WE',
      'S': 'WE', 
      'E': 'NS',
      'W': 'NS',
      'NS': 'WE',
      'WE': 'NS'
    };
    return perpendicularMap[direction] || 'NS';
  }

  // ------------ MÉTHODES POUR LES FEUX PIÉTONS ---------------  


  isPedestrianSynced(direction: Direction): boolean {
  const vehicleState = this.getLightStateFromSumo(direction);
  const pedestrianState = this.getPedestrianLightState(direction);
  
  // NOUVELLE LOGIQUE : Piétons mêmes directions que véhicules
  // Si véhicules verts → piétons mêmes directions devraient être verts
  // Si véhicules rouges → piétons mêmes directions devraient être rouges
  
  if (vehicleState === 'green' && pedestrianState === 'green') {
    return true; // Bonne synchronisation : véhicules et piétons mêmes directions verts
  }
  
  if (vehicleState === 'red' && pedestrianState === 'red') {
    return true; // Bonne synchronisation : véhicules et piétons mêmes directions rouges
  }
  
  // Cas de désynchronisation
  return false;
}

getPedestrianSyncInfo(direction: Direction): string {
  return this.isPedestrianSynced(direction) ? '✅ Sync' : '❌ Désync';
}


  // Méthode pour la couleur des feux véhicules
  getLightColorFromSumo(direction: Direction): string {
    const state = this.getLightStateFromSumo(direction);
    switch (state) {
      case 'green': return 'bg-green-500 shadow-lg shadow-green-500/50';
      case 'yellow': return 'bg-yellow-400 shadow-lg shadow-yellow-400/50';
      case 'red': return 'bg-red-500 shadow-lg shadow-red-500/50';
      default: return 'bg-gray-600';
    }
  }

  // Méthode pour debuguer la synchronisation
checkAllPedestrianSync(): void {
  console.log('🔍 Vérification synchronisation piétons/véhicules:');
  
  this.directions.forEach(dir => {
    const vehicleState = this.getLightStateFromSumo(dir);
    const pedestrianState = this.getPedestrianLightState(dir);
    const isSynced = this.isPedestrianSynced(dir);
    
    console.log(`🎯 ${dir}: Véhicules=${vehicleState}, Piétons=${pedestrianState}, Sync=${isSynced}`);
  });
}

getLightIcon(direction: Direction): string {
  if (!this.traffic_light?.state_by_direction?.vehicles) {
    return '🚦'; // Icône par défaut
  }

  const sumoDirection = this.getSumoDirection(direction);
  const sumoState = this.traffic_light.state_by_direction.vehicles[sumoDirection];
  const lightState = this.getLightStateFromSumo(direction);

  // Icônes basées sur l'état SUMO exact
  switch (sumoState) {
    case 'G': // Vert fléché (prioritaire)
      return '🟢'; // ou '➡️' pour plus de précision
    case 'g': // Vert normal
      return '🟢';
    case 'y': // Jaune
    case 'Y': // Jaune clignotant
      return '🟡';
    case 'r': // Rouge
      return '🔴';
    case 'R': // Rouge strict
      return '🔴';
    default:
      return '🚦';
  }
}

getLightStateDescription(direction: Direction): string {
  if (!this.traffic_light?.state_by_direction?.vehicles) {
    return 'État inconnu';
  }

  const sumoDirection = this.getSumoDirection(direction);
  const sumoState = this.traffic_light.state_by_direction.vehicles[sumoDirection];

  switch (sumoState) {
    case 'G': return 'Vert fléché (prioritaire)';
    case 'g': return 'Vert (autorisation)';
    case 'y': return 'Jaune (attention)';
    case 'Y': return 'Jaune clignotant';
    case 'r': return 'Rouge (arrêt)';
    case 'R': return 'Rouge strict';
    case 's': return 'Arrêt (stop)';
    case 'u': return 'Non régulé';
    case 'o': return 'Orange clignotant';
    case 'O': return 'Orange';
    default: return `État: ${sumoState}`;
  }
}

getPedestrianStateDescription(direction: Direction): string {
  const state = this.getPedestrianLightState(direction);
  const sumoDirection = this.getSumoDirection(direction);
  const sumoState = this.traffic_light?.state_by_direction?.pedestrians?.[sumoDirection];
  
  if (state === 'green') {
    return sumoState === 'G' ? 'Traversée prioritaire' : 'Traversée autorisée';
  } else {
    return 'Traversée interdite';
  }
}

clearMessage(): void {
  this.message = '';
}

  // ------------ MÉTHODES POUR L'INTERFACE SIMPLIFIÉE ---------------

  getLightColor(direction: Direction): string {
    const state = this.getLightStateFromSumo(direction);
    switch (state) {
      case 'green': return 'bg-green-500 shadow-lg shadow-green-500/50';
      case 'yellow': return 'bg-yellow-400 shadow-lg shadow-yellow-400/50';
      case 'red': return 'bg-red-500 shadow-lg shadow-red-500/50';
      default: return 'bg-gray-600';
    }
  }

  getArrowColor(direction: Direction, arrowType: 'straight' | 'right'): string {
    // Logique simplifiée pour les flèches
    // En réalité, vous devriez analyser l'état SUMO spécifique
    const vehicleState = this.getLightStateFromSumo(direction);
    
    if (vehicleState === 'green') {
      return 'bg-green-500 text-white border-green-400';
    } else if (vehicleState === 'yellow') {
      return 'bg-yellow-500 text-white border-yellow-400';
    } else {
      return 'bg-gray-700 text-gray-500 border-gray-600';
    }
  }

  // Contrôle des feux fléchés
  setArrowLight(direction: Direction, arrowType: 'straight' | 'right'): void {
    // Implémentez la logique pour contrôler les feux fléchés
    this.flash(`🔄 Flèche ${arrowType} ${direction} activée`);
    // TODO: Appeler l'API backend pour les feux fléchés
  }


// Méthode avec délai entre les requêtes
// Avec un délai très court (50ms)
activateMultipleLanesQuick(indexes: number[]): Observable<any> {
  return new Observable(observer => {
    let completed = 0;
    
    indexes.forEach((index, i) => {
      setTimeout(() => {
        this.simulationService.prioritizeLane(index).subscribe({
          next: (response) => {
            completed++;
            if (completed === indexes.length) {
              observer.next(response);
              observer.complete();
            }
          },
          error: (err) => {
            completed++;
            if (completed === indexes.length) {
              observer.error(err);
            }
          }
        });
      }, i * 50); // Seulement 50ms de délai
    });
  });
}


debugLaneIndexes(): void {
  console.log('🎯 INDEX DES VOIES:');
  
  this.directions.forEach(dir => {
    const indexes = this.laneIndexes[dir];
    console.log(`📍 ${dir}: Tout droit=${indexes.straight}, Droite=${indexes.right}`);
  });
  
  // Afficher aussi les données SUMO pour vérifier
  console.log('Données SUMO lanes:', this.tl_lanes);
}

// Variables pour le test
lastTestedIndex: number | null = null;

// Méthode pour générer une plage d'index
getIndexRange(start: number, end: number): number[] {
  return Array.from({length: end - start + 1}, (_, i) => start + i);
}

// Méthode pour tester un index
testIndex(index: number): void {
  this.lastTestedIndex = index;
  console.log(`🧪 Test index ${index}`);
  
  this.simulationService.prioritizeLane(index).subscribe({
    next: (response) => {
      console.log(`✅ Index ${index} valide`, response);
      // Recharger les données après un délai
      setTimeout(() => this.loadCarrefourData(), 1000);
    },
    error: (err) => {
      console.log(`❌ Index ${index} invalide`);
    }
  });
}

// ------------ MÉTHODES PIÉTONS SIMPLIFIÉES ---------------

// Obtenir l'index piéton d'une direction
getPedestrianIndex(direction: Direction): number {
  return this.pedestrianIndexes[direction] || -1;
}

// Méthodes existantes à garder
getPedestrianLightColor(direction: Direction): string {
  const state = this.getPedestrianLightState(direction);
  return state === 'green' 
    ? 'bg-green-500 shadow-lg shadow-green-500/50' 
    : 'bg-red-500 shadow-lg shadow-red-500/50';
}


// ------------ MÉTHODES PIÉTONS MANQUANTES ---------------

// Obtenir la direction à partir de l'ID de voie
getPedestrianDirection(laneId: string): string {
  const id = laneId.toLowerCase();
  
  if (id.includes('nord') || id.includes('north') || id.includes('n_')) {
    return 'NORD';
  }
  if (id.includes('sud') || id.includes('south') || id.includes('s_')) {
    return 'SUD';
  }
  if (id.includes('est') || id.includes('east') || id.includes('e_')) {
    return 'EST';
  }
  if (id.includes('ouest') || id.includes('west') || id.includes('w_')) {
    return 'OUEST';
  }
  
  // Fallback: essayer de deviner à partir des premiers caractères
  if (id.startsWith('n')) return 'NORD';
  if (id.startsWith('s')) return 'SUD';
  if (id.startsWith('e')) return 'EST';
  if (id.startsWith('w') || id.startsWith('o')) return 'OUEST';
  
  return laneId; // Retourner l'ID original si on ne peut pas déterminer
}

// Méthode pour obtenir l'icône piéton (si vous voulez l'utiliser)
getPedestrianLightIcon(direction: Direction): string {
  const state = this.getPedestrianLightState(direction);
  return state === 'green' ? '🚶‍♂️🟢' : '🚶‍♂️🔴';
}

// Nombre de piétons par direction (à partir des données SUMO)
getPedestrianCount(direction: Direction): number {
  const pedestrianLanes = this.getPedestrianLanes();
  return pedestrianLanes
    .filter(lane => this.getPedestrianDirection(lane.id) === direction)
    .reduce((total, lane) => total + lane.num_vehicles, 0);
}


// Méthode de debug pour voir les données piétons
debugPedestrianData(): void {
  console.log('🔍 DEBUG DONNÉES PIÉTONS SUMO:');
  console.log('Traffic light:', this.traffic_light);
  console.log('State by direction:', this.traffic_light?.state_by_direction);
  console.log('Pedestrians state:', this.traffic_light?.state_by_direction?.pedestrians);
  console.log('All lanes:', this.tl_lanes);
  
  // Afficher l'état de chaque direction
  this.directions.forEach(dir => {
    const sumoDir = this.getSumoDirection(dir);
    const vehicleState = this.traffic_light?.state_by_direction?.vehicles?.[sumoDir];
    const pedestrianState = this.traffic_light?.state_by_direction?.pedestrians?.[sumoDir];
    
    console.log(`📍 ${dir} (${sumoDir}):`);
    console.log(`   Véhicules: ${vehicleState}`);
    console.log(`   Piétons: ${pedestrianState}`);
    console.log(`   Interface: ${this.getPedestrianLightState(dir)}`);
  });
}

// Logique pour déterminer si les piétons perpendiculaires sont verts
private isPerpendicularPedestrianGreen(direction: Direction): boolean {
  // Quand véhicules Nord-Sud rouges → piétons Est-Ouest verts
  // Quand véhicules Est-Ouest rouges → piétons Nord-Sud verts
  const isNorthSouth = direction === 'NORD' || direction === 'SUD';
  const isEastWest = direction === 'EST' || direction === 'OUEST';
  
  if (isNorthSouth) {
    // Pour Nord-Sud, vérifier si Est ou Ouest ont des véhicules verts
    const eastState = this.getLightStateFromSumo('EST');
    const westState = this.getLightStateFromSumo('OUEST');
    return eastState === 'green' || westState === 'green';
  }
  
  if (isEastWest) {
    // Pour Est-Ouest, vérifier si Nord ou Sud ont des véhicules verts
    const northState = this.getLightStateFromSumo('NORD');
    const southState = this.getLightStateFromSumo('SUD');
    return northState === 'green' || southState === 'green';
  }
  
  return false;
}

// Dans app.ts - Assurez-vous que le rafraîchissement est activé
private startDynamicDataRefresh(): void {
  this.stopDynamicDataRefresh();
  this.refreshInterval = interval(1000).subscribe(() => {
    this.simulationService.getDynamicCarrefourData().subscribe({
      next: (data) => {
        if (data.sumo === 'inactive') {
          this.stopDynamicDataRefresh();
          this.simulationRunning = false;
          return;
        }
        this.processSumoData(data);
      },
      error: (err) => console.error('Erreur rafraîchissement:', err),
    });
  });
} 

// Version encore plus simple pour debug
getPedestrianLightStateSimple(direction: Direction): LightState {
  const pedestrianLanes = this.tl_lanes.filter(lane => 
    lane.type === 'pieton' && this.getPedestrianDirection(lane.id) === direction
  );
  
  if (pedestrianLanes.length > 0) {
    return pedestrianLanes[0].signal === 'G' ? 'green' : 'red';
  }
  
  return 'red';
}


// Méthode utilitaire corrigée
getPedestrianLanesForDirection(direction: Direction): TrafficLightLane[] {
  return this.tl_lanes.filter(lane => {
    if (lane.type !== 'pieton') return false;
    
    const laneDirection = this.getPedestrianDirection(lane.id);
    return laneDirection === direction;
  });
}

// Méthode de debug spécifique pour les piétons
debugPedestrianStates(): void {
  console.log('🔍 DEBUG ÉTATS PIÉTONS EXACTS:');
  
  this.directions.forEach(dir => {
    const pedestrianLanes = this.getPedestrianLanesForDirection(dir);
    console.log(`📍 ${dir}:`);
    
    if (pedestrianLanes.length > 0) {
      pedestrianLanes.forEach(lane => {
        console.log(`   🚶 Voie ${lane.id}: signal=${lane.signal}, véhicules=${lane.num_vehicles}`);
      });
    } else {
      console.log(`   ❌ Aucune voie piéton trouvée pour ${dir}`);
    }
    
    // Afficher aussi l'état calculé
    console.log(`   🎯 État calculé: ${this.getPedestrianLightState(dir)}`);
  });
}

// Méthode de rafraîchissement forcé
forceRefresh(): void {
  console.log('🔄 FORCE REFRESH - Rechargement manuel');
  this.flash('🔄 Actualisation des données...');
  
  // Double rafraîchissement pour être sûr
  this.loadCarrefourData();
  setTimeout(() => this.loadCarrefourData(), 300);
}

// Méthode pour obtenir l'état piéton en utilisant les index connus
getPedestrianLightState(direction: Direction): LightState {
  const pedestrianIndex = this.getPedestrianIndex(direction);
  
  if (pedestrianIndex === -1) {
    console.warn(`❌ Index piéton non configuré pour ${direction}`);
    return 'red';
  }
  
  // Trouver la voie avec cet index
  const pedestrianLane = this.tl_lanes.find(lane => {
    // Comparer par index si disponible, sinon par ID
    return lane.index === pedestrianIndex || 
           lane.id.includes(pedestrianIndex.toString());
  });
  
  if (!pedestrianLane) {
    // console.warn(`❌ Aucune voie trouvée pour l'index ${pedestrianIndex} (${direction})`);
    return 'red';
  }
  
  // console.log(`🎯 ${direction} - Index: ${pedestrianIndex}, Signal: ${pedestrianLane.signal}`);
  
  // Conversion directe du signal
  if (pedestrianLane.signal === 'G' || pedestrianLane.signal === 'g') {
    return 'green';
  } else {
    return 'red';
  }
}

// Obtenir les informations de la voie piétonne
getPedestrianLaneInfo(direction: Direction): any {
  const index = this.getPedestrianIndex(direction);
  
  if (index === -1) return null;
  
  return this.tl_lanes.find(lane => 
    lane.index === index || lane.id.includes(index.toString())
  );
}

// Dans app.ts - Implémentation des commandes globales

// Activer tous les passages piétons
activateAllPedestrians(): void {
  const allIndexes = [
    this.pedestrianIndexes['NORD'],
    this.pedestrianIndexes['SUD'], 
    this.pedestrianIndexes['EST'],
    this.pedestrianIndexes['OUEST']
  ].filter(index => index !== undefined && index !== -1);
  
  console.log('🎯 Activation tous piétons:', allIndexes);
  
  if (allIndexes.length === 0) {
    this.flash('❌ Aucun index piéton configuré');
    return;
  }
  
  // Activer tous les index piétons
  this.activateMultipleLanes(allIndexes, 100).then(responses => {
    this.flash('🟢 Tous les passages piétons activés');
    setTimeout(() => this.loadCarrefourData(), 1000);
  }).catch(error => {
    this.handleError('Erreur activation piétons', error);
  });
}

// Prioriser les passages NORD-SUD
prioritizePedestrianCrossing(direction: string): void {
  let indexes: number[] = [];
  let message = '';
  
  if (direction === 'NS') {
    indexes = [
      this.pedestrianIndexes['NORD'],
      this.pedestrianIndexes['SUD']
    ].filter(index => index !== undefined && index !== -1);
    message = '🚶‍♂️ Passages NORD-SUD priorisés';
  } else if (direction === 'WE') {
    indexes = [
      this.pedestrianIndexes['EST'],
      this.pedestrianIndexes['OUEST']
    ].filter(index => index !== undefined && index !== -1);
    message = '🚶‍♂️ Passages EST-OUEST priorisés';
  }
  
  if (indexes.length === 0) {
    this.flash(`❌ Aucun index configuré pour ${direction}`);
    return;
  }
  
  console.log(`🎯 Activation piétons ${direction}:`, indexes);
  
  this.activateMultipleLanes(indexes, 100).then(responses => {
    this.flash(message);
    setTimeout(() => this.loadCarrefourData(), 1000);
  }).catch(error => {
    this.handleError(`Erreur piétons ${direction}`, error);
  });
}

// Arrêter tous les passages piétons (version améliorée)
stopAllPedestrians(): void {
  // Pour arrêter les piétons, on active les véhicules
  // Cela mettra automatiquement les piétons au rouge
  this.simulationService.prioritizeLaneByDirection('NS').subscribe({
    next: (response) => {
      this.flash('🔴 Tous les passages piétons arrêtés');
      setTimeout(() => this.loadCarrefourData(), 1000);
    },
    error: (err) => {
      this.handleError('Erreur arrêt piétons', err);
    }
  });
}

// Méthode pour activer plusieurs index avec délai
private async activateMultipleLanes(indexes: number[], delayMs: number = 100): Promise<any[]> {
  const results = [];
  
  for (let i = 0; i < indexes.length; i++) {
    try {
      const result = await this.simulationService.prioritizeLane(indexes[i]).toPromise();
      results.push(result);
      console.log(`✅ Index ${indexes[i]} activé (${i + 1}/${indexes.length})`);
      
      // Délai entre chaque requête
      if (i < indexes.length - 1) {
        await new Promise(resolve => setTimeout(resolve, delayMs));
      }
    } catch (error) {
      console.error(`❌ Erreur index ${indexes[i]}:`, error);
      results.push(error);
    }
  }
  
  return results;
}

// Méthodes utilisant prioritizeLaneByDirection
setStraightArrow(direction: Direction): void {
  const directionMap = {
    'NORD': 'N',
    'SUD': 'S', 
    'EST': 'E',
    'OUEST': 'W'
  };
  
  const shortDirection = directionMap[direction];
  
  console.log(`🎯 Activation ${direction} via direction: ${shortDirection}`);
  
  this.simulationService.prioritizeLaneByDirection(shortDirection).subscribe({
    next: (response) => {
      console.log(`✅ ${direction} activé via direction API`);
      this.flash(`🟢 ${direction} activé`);
      setTimeout(() => this.loadCarrefourData(), 1000);
    },
    error: (err) => {
      console.error(`❌ Erreur ${direction}:`, err);
      this.handleError(`Erreur ${direction}`, err);
    }
  });
}

// Commandes globales utilisant prioritizeLaneByDirection
setNSGreen(): void {
  this.simulationService.prioritizeLaneByDirection('NS').subscribe({
    next: (response) => {
      this.flash('🟢 NORD-SUD activé');
      setTimeout(() => this.loadCarrefourData(), 1000);
    },
    error: (err) => this.handleError('Erreur NORD-SUD', err)
  });
}

setEWGreen(): void {
  this.simulationService.prioritizeLaneByDirection('WE').subscribe({
    next: (response) => {
      this.flash('🟢 EST-OUEST activé');
      setTimeout(() => this.loadCarrefourData(), 1000);
    },
    error: (err) => this.handleError('Erreur EST-OUEST', err)
  });
}

// Pour les piétons, on garde la méthode par index
prioritizePedestrianDirection(direction: Direction): void {
  const index = this.getPedestrianIndex(direction);
  
  if (index === -1) {
    this.flash(`❌ Pas d'index piéton configuré pour ${direction}`);
    return;
  }
  
  console.log(`🎯 Activation piétons ${direction}: index ${index}`);
  
  this.simulationService.prioritizeLane(index).subscribe({
    next: (response) => {
      this.flash(`🚶‍♂️ Piétons ${direction} activés`);
      setTimeout(() => this.loadCarrefourData(), 1000);
    },
    error: (err) => {
      this.handleError(`Erreur piétons ${direction}`, err);
    }
  });
}

// Pour les virages droits (si vous en avez)
setRightArrow(direction: Direction): void {
  // Prendre directement le premier élément si c'est un tableau
  const rightIndex = this.laneIndexes[direction]?.right;
  const index = Array.isArray(rightIndex) ? rightIndex[0] : rightIndex;
  
  this.simulationService.prioritizeLane(index).subscribe({
    next: (response) => {
      this.flash(`🔵 Virage droite ${direction} activé`);
      setTimeout(() => this.loadCarrefourData(), 1000);
    },
    error: (err) => {
      this.handleError(`Erreur virage droite ${direction}`, err);
    }
  });
}

// Fallback par index pour les virages
// Fallback par index pour les virages - CORRIGÉ
private prioritizeRightArrowByIndex(direction: Direction): void {
  const index = this.laneIndexes[direction]?.right; // Peut être number[] ou number
  
  if (index) {
    let indexToUse: number;
    
    // Gérer à la fois les tableaux et les nombres
    if (Array.isArray(index)) {
      // Si c'est un tableau, prendre le premier élément
      indexToUse = index[0];
    } else {
      // Si c'est un nombre, l'utiliser directement
      indexToUse = index;
    }
    
    // Vérifier que l'index est valide
    if (indexToUse !== undefined && indexToUse !== -1) {
      this.simulationService.prioritizeLane(indexToUse).subscribe({
        next: (response) => {
          this.flash(`🔵 Virage droite ${direction} activé (index)`);
          setTimeout(() => this.loadCarrefourData(), 1000);
        },
        error: (err) => this.handleError(`Erreur virage ${direction}`, err)
      });
    } else {
      this.flash(`❌ Index virage droite invalide pour ${direction}`);
    }
  } else {
    this.flash(`❌ Pas de virage droite configuré pour ${direction}`);
  }
}

  // ... le reste de vos méthodes existantes ...

  // Méthode pour les icônes des types de phases - VERSION SIMPLIFIÉE
  getPhaseTypeIcon(type: string): string {
    switch (type.toLowerCase()) {
      case 'red':
      case 'rouge':
        return '🔴';
      case 'yellow':
      case 'jaune':
        return '🟡';
      case 'green':
      case 'vert':
        return '🟢';
      default:
        return '⚪';
    }
  }

  // Méthode pour les badges des types de phases - VERSION SIMPLIFIÉE
  getPhaseTypeBadgeClass(type: string): string {
    const baseClasses = 'px-2 py-1 text-xs font-medium rounded-full';
    
    switch (type.toLowerCase()) {
      case 'red':
      case 'rouge':
        return `${baseClasses} bg-red-900 text-red-200`;
      case 'yellow':
      case 'jaune':
        return `${baseClasses} bg-yellow-900 text-yellow-200`;
      case 'green':
      case 'vert':
        return `${baseClasses} bg-green-900 text-green-200`;
      default:
        return `${baseClasses} bg-gray-700 text-gray-300`;
    }
  }

   updateGreenMainDuration() {
    if (this.greenMainDuration <= 0) {
      this.message = 'La durée vert principal doit être positive';
      return;
    }

    this.isLoading = true;
    this.simulationService.changeGreenMainPhaseDuration(this.greenMainDuration).subscribe({
      next: (response) => {
        this.message = `✅ Durée vert principal mise à jour: ${this.greenMainDuration}s`;
        this.isLoading = false;
      },
      error: (error) => {
        this.message = '❌ Erreur lors de la mise à jour vert principal';
        this.isLoading = false;
      }
    });
  }

  // Mettre à jour la durée des verts courts
  updateGreenShortDuration() {
    if (this.greenShortDuration <= 0) {
      this.message = 'La durée vert court doit être positive';
      return;
    }

    this.isLoading = true;
    this.simulationService.changeGreenShortPhaseDuration(this.greenShortDuration).subscribe({
      next: (response) => {
        this.message = `✅ Durée vert court mise à jour: ${this.greenShortDuration}s`;
        this.isLoading = false;
      },
      error: (error) => {
        this.message = '❌ Erreur lors de la mise à jour vert court';
        this.isLoading = false;
      }
    });
  }


}