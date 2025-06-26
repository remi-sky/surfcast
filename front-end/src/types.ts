// src/types.ts
export interface SummaryForecast {
    date: string;
    time: string;
    rating: 'Lake Mode' | 'Sketchy' | 'Playable' | 'Solid' | 'Firing';
    explanation: string;
    swell_wave_height: number;
    swell_wave_peak_period?: number;
    wind_speed_kmh?: number;
    wind_type?: string;
    wind_severity?: string;
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
    swell_wave_height: number;
    swell_wave_direction?: number;
    wind_wave_height_m?: number;
    swell_wave_peak_period?: number;           // ← added
    wind_speed_kmh?: number;
    wind_direction_deg?: number;
    wind_type?: string;
    wind_severity?: string;
    explanation?: string;
    rating?: 'Lake Mode' | 'Sketchy' | 'Playable' | 'Solid' | 'Firing';
    timezone?: string;
  }
  