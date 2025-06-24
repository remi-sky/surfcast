from pydantic import BaseModel
from typing import Optional

class ForecastRequest(BaseModel):
    spot: str
    swell_height_m: float
    swell_direction_deg: float
    wind_speed_kph: float
    wind_direction_deg: float

class ForecastResponse(BaseModel):
    spot: str
    surfable: bool

class ForecastTestResponse(BaseModel):
    time: str
    swell_wave_height: float
    swell_wave_direction: float
    wind_wave_height_m: float

class SurfableForecast(BaseModel):
    spot: str
    time: Optional[str] = None
    wave_height: Optional[float] = None
    wave_direction: Optional[int] = None
    wind_wave_height: Optional[float] = None
    swell_period: Optional[float] = None
    wind_direction: Optional[int] = None
    surfable: bool
    reason: Optional[str] = None
    level: Optional[str] = None  # "Poor", "Fair", "Good", "Excellent"

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