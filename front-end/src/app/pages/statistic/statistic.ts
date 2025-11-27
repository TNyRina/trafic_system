import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { SimulationService,Simulation } from '../../simulation-service';


@Component({
  selector: 'app-statistic',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './statistic.html',
  styleUrls: ['./statistic.css']
})
export class Statistic implements OnInit {
  selectedSimulation: Simulation | null = null;
  isLoading = true;
  error: string | null = null;
simulationToDelete: { sim: Simulation, key: string } | null = null;
 simulationsData: { [key: string]: Simulation } = {};
// Et le tableau pour l'affichage
simulations: Simulation[] = [];
successMessage: string | null = null;
startDate: string = '';
endDate: string = '';
isFiltering = false;

  constructor(private simulationService: SimulationService) {}

  ngOnInit() {
    this.loadSimulations();
  }

  // loadSimulations() {
  //   this.isLoading = true;
  //   this.error = null;

  //   this.simulationService.getSimulations().subscribe({
  //     next: (data) => {
  //       this.simulationsData = data;
  //       // Convertir en tableau pour l'affichage
  //       this.simulations = Object.values(data);
  //       this.isLoading = false;
  //     },
  //     error: (err) => {
  //       this.error = 'Erreur lors du chargement des simulations';
  //       this.isLoading = false;
  //       console.error('Erreur:', err);
  //     }
  //   });
  // }

  getLanesArray(lanesStats: any): any[] {
    if (!lanesStats) return [];
    return Object.values(lanesStats);
  }

  getShortVehicleId(vehicleId: string): string {
    return vehicleId.length > 8 ? vehicleId.substring(0, 8) + '...' : vehicleId;
  }

  getActiveLanesForDirection(lanesStats: any, direction: string): number {
    const directionPrefix = this.getDirectionPrefix(direction);
    const lanes = this.getLanesArray(lanesStats);
    return lanes.filter((lane: any) => 
      lane.edge_id.includes(directionPrefix) && lane.num_vehicles > 0
    ).length;
  }

  getVehicleCountForDirection(lanesStats: any, direction: string): number {
    const directionPrefix = this.getDirectionPrefix(direction);
    const lanes = this.getLanesArray(lanesStats);
    return lanes.filter((lane: any) => 
      lane.edge_id.includes(directionPrefix)
    ).reduce((total: number, lane: any) => total + lane.num_vehicles, 0);
  }

  getAvgWaitingTimeForDirection(lanesStats: any, direction: string): number {
    const directionPrefix = this.getDirectionPrefix(direction);
    const lanes = this.getLanesArray(lanesStats).filter((lane: any) => 
      lane.edge_id.includes(directionPrefix) && lane.num_vehicles > 0
    );
    
    if (lanes.length === 0) return 0;
    
    return lanes.reduce((total: number, lane: any) => total + lane.waiting_time, 0) / lanes.length;
  }

  private getDirectionPrefix(direction: string): string {
    const prefixes: { [key: string]: string } = {
      'NORD': 'N',
      'SUD': 'S',
      'EST': 'E',
      'OUEST': 'W'
    };
    return prefixes[direction] || direction.charAt(0);
  }

  // Méthode pour formater la durée
  formatDuration(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  }

  selectSimulation(sim: Simulation) {
    this.selectedSimulation = sim;
    // Scroll vers la section détails pour une meilleure UX
    setTimeout(() => {
      const element = document.getElementById('simulation-details');
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }, 100);
  }

  // AJOUTEZ CETTE MÉTHODE MANQUANTE
  closeDetails() {
    this.selectedSimulation = null;
  }


confirmDelete(sim: Simulation) {
  // Trouver la clé correspondante ("2", "3")
  const key = this.findSimulationKey(sim);
  console.log('🎯 Supprimer simulation Key:', key, 'ID:', sim.simulation_id);
  
  if (key) {
    this.simulationToDelete = { sim: sim, key: key };
  } else {
    alert('Erreur: Impossible de trouver la clé de la simulation');
  }
}

// Méthode pour trouver la clé d'une simulation
private findSimulationKey(simulation: Simulation): string {
  for (const [key, sim] of Object.entries(this.simulationsData)) {
    if (sim.simulation_id === simulation.simulation_id) {
      return key;
    }
  }
  return '';
}

deleteSimulation() {
  if (this.simulationToDelete) {
    const simulationKey = this.simulationToDelete.key;
    const simulationId = this.simulationToDelete.sim.simulation_id;
    
    this.simulationService.deleteSimulation(simulationKey).subscribe({
      next: () => {
        this.successMessage = `✅ Simulation #${simulationId} supprimée avec succès`;
        this.loadSimulations();
        this.simulationToDelete = null;
        
        // Effacer le message après 3 secondes
        setTimeout(() => {
          this.successMessage = null;
        }, 3000);
      },
      error: (err) => {
        console.error('Erreur suppression:', err);
        alert('Erreur lors de la suppression');
        this.simulationToDelete = null;
      }
    });
  }
}

// Ajoutez cette méthode pour fermer le message
clearSuccessMessage() {
  this.successMessage = null;
}

// Ajoutez cette méthode pour annuler
cancelDelete() {
  this.simulationToDelete = null;
}

// Méthode pour obtenir le label français de la voie
getLaneLabel(laneId: string): string {
  const laneLabels: { [key: string]: string } = {
    'N2C_1': 'Nord → Droite',
    'N2C_2': 'Nord → Tout droit', 
    'E2C_1': 'Est → Droite',
    'E2C_2': 'Est → Tout droit',
    'S2C_1': 'Sud → Droite',
    'S2C_2': 'Sud → Tout droit',
    'W2C_1': 'Ouest → Droite',
    'W2C_2': 'Ouest → Tout droit',
    
    // Vous pouvez ajouter d'autres voies si nécessaire
    'N2C_0': 'Nord → Gauche',
    'E2C_0': 'Est → Gauche', 
    'S2C_0': 'Sud → Gauche',
    'W2C_0': 'Ouest → Gauche',
    
    // Voies de sortie
    'C2N_1': '→ Nord',
    'C2N_2': '→ Nord',
    'C2E_1': '→ Est',
    'C2E_2': '→ Est',
    'C2S_1': '→ Sud', 
    'C2S_2': '→ Sud',
    'C2W_1': '→ Ouest',
    'C2W_2': '→ Ouest'
  };

  return laneLabels[laneId] || laneId;
}

// Méthode pour obtenir l'emoji de direction
getLaneEmoji(laneId: string): string {
  const emojiMap: { [key: string]: string } = {
    'N2C_1': '⬇️↘️',
    'N2C_2': '⬇️⬇️',
    'E2C_1': '⬅️↙️', 
    'E2C_2': '⬅️⬅️',
    'S2C_1': '⬆️↖️',
    'S2C_2': '⬆️⬆️',
    'W2C_1': '➡️↗️',
    'W2C_2': '➡️➡️'
  };

  return emojiMap[laneId] || '🛣️';
}

// Méthodes de filtrage
applyDateFilter() {
  this.isLoading = true;
  this.isFiltering = true;
  
  this.simulationService.filterByDate(
    this.startDate || undefined, 
    this.endDate || undefined
  ).subscribe({
    next: (data) => {
      this.simulationsData = data;
      this.simulations = Object.values(data);
      this.isLoading = false;
    },
    error: (err) => {
      this.error = 'Erreur lors du filtrage';
      this.isLoading = false;
      console.error('Erreur filtrage:', err);
    }
  });
}

// Réinitialiser le filtre
resetFilter() {
  this.startDate = '';
  this.endDate = '';
  this.isFiltering = false;
  this.loadSimulations();
}

// Formater la date pour l'affichage
formatDateForInput(dateString: string): string {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toISOString().split('T')[0];
}

loadSimulations() {
  this.isLoading = true;
  this.error = null;

  this.simulationService.getAllSimulations().subscribe({
    next: (data) => {
      this.simulationsData = data;
      this.simulations = Object.values(data);
      this.isLoading = false;
      this.isFiltering = false;
    },
    error: (err) => {
      this.error = 'Erreur lors du chargement des simulations';
      this.isLoading = false;
      console.error('Erreur:', err);
    }
  });
}

}