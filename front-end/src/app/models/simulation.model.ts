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