// src/types.ts
export interface SummaryForecast {
    date: string;
    time: string;
    rating: 'Poor' | 'Fair' | 'Good' | 'Excellent';
    explanation: string;
  }
  
  export interface Spot {
    id: string;
    name: string;
    region: string;
    lat: number;
    lon: number;
    forecasts: SummaryForecast[];
  }
  
  export interface Location {
    lat: number;
    lon: number;
    name: string;
  }
  
  export interface SurfForecast {
    time: string;
    wave_height_m: number;
    wave_direction_deg?: number;
    wind_wave_height_m?: number;
    wave_period_s?: number;           // ← added
    wind_speed_kmh?: number;
    wind_direction_deg?: number;
    wind_type?: string;
    explanation?: string;
    rating?: 'Poor' | 'Fair' | 'Good' | 'Excellent';
    timezone?: string;
  }
  