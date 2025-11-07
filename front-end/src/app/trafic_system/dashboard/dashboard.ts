import { Component, OnDestroy } from '@angular/core';
import { SimulationService } from '../../simulation-service';
import { interval, Subscription } from 'rxjs';
import { CommonModule } from '@angular/common';


@Component({
  selector: 'app-dashboard',
  imports: [ CommonModule ],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})

export class Dashboard implements OnDestroy {
  message = '';
  carrefour: any;
  edges: any;
  lanes: any;
  tl_lanes: any;
  traffic_light:any;
  pedestrians:any;
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
        
        this.traffic_light = data.traffic_light_info;
        this.tl_lanes = Object.values(data.traffic_light_info.lanes);
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

  stopTL(): void{
    this.simulationService.stopTrafficLight().subscribe({
      next: (response) => {
        this.updateMessage('✅ Toutes les voies sont stopees !');
        console.log(response);
      },
      error: (err) => this.handleError('❌ impossible de stoper toutes les voies', err),
    });
  }

  restoreTL(): void{
    this.simulationService.restoreTrafficLight().subscribe({
      next: (response) => {
        this.updateMessage('✅ TL restaure !');
        console.log(response);
      },
      error: (err) => this.handleError('❌ impossible de restaurer TL', err),
    });
  }

  prioritizeLane(index: number): void{
    this.simulationService.prioritizeLane(index).subscribe({
      next: (response) => {
        this.updateMessage(`✅  ${index} priorite !`);
        console.log(response);
      },
      error: (err) => this.handleError(`❌ impossible de prioriser ${index} `, err),
    });
  }

  prioritizeLaneByDirection(direction: string): void{
    this.simulationService.prioritizeLaneByDirection(direction).subscribe({
      next: (response) => {
        this.updateMessage(`✅  ${direction} priorite !`);
        console.log(response);
      },
      error: (err) => this.handleError(`❌ impossible de prioriser ${direction} `, err),
    });
  }


  private startDynamicDataRefresh(): void {
    this.stopDynamicDataRefresh();

    this.refreshInterval = interval(1000).subscribe(() => {
      this.simulationService.getDynamicCarrefourData().subscribe({
        next: (data) => {
            if(data.sumo == 'inactive') this.stopDynamicDataRefresh();
            
            this.carrefour = data;


            console.log('♻️ Données dynamiques mises à jour :', data);

            this.traffic_light = data.traffic_light_info;
            this.tl_lanes = Object.values(data.traffic_light_info.lanes);
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

