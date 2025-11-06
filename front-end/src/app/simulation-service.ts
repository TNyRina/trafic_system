import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class SimulationService {
  private apiUrl = 'http://localhost:8000/dashboard'; 
  constructor(private http: HttpClient) {}

  startSimulation(): Observable<any> {
    return this.http.get(`${this.apiUrl}/start`);
  }

  getStaticCarrefourData(): Observable<any> {
    return this.http.get(`${this.apiUrl}/`);
  }

  getDynamicCarrefourData(): Observable<any> {
    return this.http.get(`${this.apiUrl}/data`);
  }
}
