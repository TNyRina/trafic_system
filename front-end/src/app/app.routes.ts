import { Routes } from '@angular/router';
import { Statistic } from './pages/statistic/statistic';
import { Home } from './pages/home/home/home';

export const routes: Routes = [
    { path: '', component: Home },
    { path: 'statistics', component: Statistic },
];
