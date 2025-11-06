import { Component, OnDestroy } from '@angular/core';
import { SimulationService } from '../../simulation-service';
import { interval, Subscription } from 'rxjs';

@Component({
  selector: 'app-dashboard',
  imports: [],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements OnDestroy {
  message = '';
  carrefour: any;
  private refreshInterval?: Subscription; 

  constructor(private simulationService: SimulationService) {}

  ngOnInit(): void {
    this.loadCarrefourData();
  }

  private loadCarrefourData(): void {
    this.simulationService.getStaticCarrefourData().subscribe({
      next: (data) => {
        this.carrefour = data;
        console.log('✅ Données statiques chargées :', data);
      },
      error: (err) => this.handleError('Erreur lors du chargement des données', err),
    });
  }

  startSimulation(): void {
    this.updateMessage('Démarrage de la simulation...');

    this.simulationService.startSimulation().subscribe({
      next: (response) => {
        this.updateMessage('✅ Simulation démarrée avec succès !');
        console.log(response);
        this.startDynamicDataRefresh(); 
      },
      error: (err) => this.handleError('❌ Erreur lors du démarrage de la simulation', err),
    });
  }

  private startDynamicDataRefresh(): void {
    this.stopDynamicDataRefresh();

    this.refreshInterval = interval(2000).subscribe(() => {
      this.simulationService.getDynamicCarrefourData().subscribe({
        next: (data) => {
          this.carrefour = data;
          console.log('♻️ Données dynamiques mises à jour :', data);
          if(data.sumo == 'inactive') this.stopDynamicDataRefresh();
        },
        error: (err) => this.handleError('Erreur lors de la mise à jour dynamique', err),
      });
    });
  }

  private stopDynamicDataRefresh(): void {
    if (this.refreshInterval) {
      this.refreshInterval.unsubscribe();
      this.refreshInterval = undefined;
    }
  }

  private updateMessage(msg: string): void {
    this.message = msg;
  }

  private handleError(context: string, error: any): void {
    console.error(context, error);
    this.updateMessage(context);
  }

  ngOnDestroy(): void {
    this.stopDynamicDataRefresh();
  }
}

