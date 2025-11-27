import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { HttpHeaders } from '@angular/common/http';
// import { Simulation } from './models/simulation.model';


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


export interface Simulation {
  simulation_id: number;
  nom: string;
  date_debut: string;
  date_fin: string;
  duree_simulation: number;
  nb_vehicules_total: number;
  nb_pietons_total: number;
  mean_speed_global: number;
  occupancy_global: number;
  directional_stats: any;
  lanes_stats: { [key: string]: any };
  _key?: string;
}

@Injectable({
  providedIn: 'root'
})
export class SimulationService {
  private apiUrl = 'http://localhost:8000/dashboard'; 
  constructor(private http: HttpClient) {}

  // Ajoutez cette méthode pour récupérer le token CSRF
  private getCsrfToken(): string {
    const name = 'csrftoken';
    let cookieValue = '';
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  startSimulation(): Observable<any> {
    return this.http.get(`${this.apiUrl}/start`);
  }

  stopSimulation(): Observable<any> {
    return this.http.get(`${this.apiUrl}/stop`);
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


  getStatistics() {
    return this.http.get<Simulation[]>(`${this.apiUrl}/statistics/`);
  }

    // Récupérer toutes les simulations
  getSimulations(): Observable<{ [key: string]: Simulation }> {
    return this.http.get<{ [key: string]: Simulation }>(`${this.apiUrl}/statistics/`);
  }

  // Récupérer une simulation spécifique
  getSimulationById(id: number): Observable<Simulation> {
    return this.http.get<Simulation>(`${this.apiUrl}/simulations/${id}`);
  }

  deleteSimulation(key: string): Observable<any> {
  const headers = new HttpHeaders({
    'X-CSRFToken': this.getCsrfToken()
  });

  // Convertir la clé string en number si nécessaire
  const numericKey = parseInt(key, 10);
  return this.http.get(`${this.apiUrl}/statistic/delete/${numericKey}/`, { headers, withCredentials: true });
}

// Filtrage par date
filterByDate(startDate?: string, endDate?: string): Observable<{ [key: string]: Simulation }> {
  let url = `${this.apiUrl}/statistic/filter/date/`;
  
  // Construire l'URL avec les paramètres
  const params = [];
  if (startDate) params.push(`start_date=${startDate}`);
  if (endDate) params.push(`end_date=${endDate}`);
  
  if (params.length > 0) {
    url += `?${params.join('&')}`;
  }
  
  return this.http.get<{ [key: string]: Simulation }>(url);
}

// Réinitialiser (toutes les simulations)
getAllSimulations(): Observable<{ [key: string]: Simulation }> {
  return this.http.get<{ [key: string]: Simulation }>(`${this.apiUrl}/statistics/`);
}

  
}
