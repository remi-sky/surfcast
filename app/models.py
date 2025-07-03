from typing import Optional, List
from pydantic import BaseModel, EmailStr


class MarineForecast(BaseModel):
    time: str
    swell_wave_height: float
    swell_wave_direction: Optional[float] = None
    wind_wave_height_m: Optional[float] = None
    wind_swell_wave_direction: Optional[float] = None
    swell_wave_peak_period: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    wind_direction_deg: Optional[float] = None

class SurfForecast(BaseModel):
    time: str
    swell_wave_height: float
    timezone: Optional[str] = None
    swell_wave_direction: Optional[float] = None
    wind_wave_height_m: Optional[float] = None
    swell_wave_peak_period: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    wind_type: Optional[str] = None  # "offshore", "cross-shore", "onshore", "glassy", "unknown"
    wind_severity: Optional[str] = None  # "light", "breezy", "strong", "none"
    explanation: Optional[str] = None
    rating: Optional[str] = None  # "Lake mode", "Sketchy", "Playable", "Solid", "Firing"

class SurfAlertCreate(BaseModel):
    email: EmailStr
    town: str
    lat: float
    lon: float
    radius_km: float
    quality_levels: List[str]
    region: str
    country: str