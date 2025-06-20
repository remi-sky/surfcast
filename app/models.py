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
    wave_height_m: float
    wave_direction_deg: float
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
    wave_height_m: float
    wave_direction_deg: Optional[float] = None
    wind_wave_height_m: Optional[float] = None
    wind_wave_direction_deg: Optional[float] = None
    wave_period_s: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    wind_direction_deg: Optional[float] = None

class SurfForecast(BaseModel):
    time: str
    wave_height_m: float
    timezone: Optional[str] = None
    wave_direction_deg: Optional[float] = None
    wind_wave_height_m: Optional[float] = None
    wave_period_s: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    wind_type: Optional[str] = None  # "offshore", "cross-shore", "onshore", "glassy", "unknown"
    explanation: Optional[str] = None
    rating: Optional[str] = None  # "Poor", "Fair", "Good", "Excellent"