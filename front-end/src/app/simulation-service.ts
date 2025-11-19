import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';


export interface PhaseConfiguration {
  phase_index: number;
  duration: number;
  type: string;
  description: string;
}

export interface PhaseUpdateResponse {
  status: string;
  phase_index: number;
  new_duration: number;
  updated_configuration: any;
}

@Injectable({
  providedIn: 'root'
})
export class SimulationService {
  private apiUrl = 'http://localhost:8000/dashboard'; 
  constructor(private http: HttpClient) {}

  startSimulation(): Observable<any> {
    return this.http.get(`${this.apiUrl}/start`);
  }

  stopTrafficLight(): Observable<any> {
    return this.http.get(`${this.apiUrl}/traffic_light/stop_all`);
  }

  prioritizeLane(index_lane: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/traffic_light/prioritize/${index_lane}`);
  }

  prioritizeLaneByDirection(direction: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/traffic_light/prioritize_direction/${direction}`);
  }

  restoreTrafficLight(): Observable<any> {
    return this.http.get(`${this.apiUrl}/traffic_light/restore_controle`);
  }

  getStaticCarrefourData(): Observable<any> {
    return this.http.get(`${this.apiUrl}/`);
  }

  getDynamicCarrefourData(): Observable<any> {
    return this.http.get(`${this.apiUrl}/data`);
  }

  // Méthodes utilitaires pour les phases
  changePhase(phaseIndex: number): Observable<any> {
    // Utiliser l'endpoint GET existant avec durée par défaut de 30 secondes
    return this.http.get(`${this.apiUrl}/traffic_light/change_phase/${phaseIndex}/30/`);
  }

  updatePhaseDuration(phaseIndex: number, duration: number): Observable<any> {
    return this.http.put(`${this.apiUrl}/traffic_light/phase_duration`, {
      phase_index: phaseIndex,
      duration: duration
    });
  }

  // Gestion d'erreur améliorée
  private handleError(error: any): Observable<never> {
    console.error('Erreur SimulationService:', error);
    throw error;
  }

   // Configuration par groupes de phases
  changeYellowPhaseDuration(duration: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/traffic_light/change_phase/yellow/${duration}/`);
  }

  changeGreenMainPhaseDuration(duration: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/traffic_light/change_phase/green_main/${duration}/`);
  }

  changeGreenShortPhaseDuration(duration: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/traffic_light/change_phase/green_short/${duration}/`);
  }

  // Configuration individuelle des phases
  changePhaseDuration(phaseIndex: number, duration: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/traffic_light/change_phase/${phaseIndex}/${duration}/`, {});
  }

  // Arrêt tous feux
  stopAllTl(): Observable<any> {
    return this.http.get(`${this.apiUrl}/traffic_light/stop_all`);
  }

  // Rétablir contrôle
  restoreControleTl(): Observable<any> {
    return this.http.get(`${this.apiUrl}/traffic_light/restore_controle`);
  }
  
}
