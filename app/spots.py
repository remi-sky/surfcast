from pydantic import BaseModel
from typing import Tuple, List

class SurfSpot(BaseModel):
    name: str
    lat: float
    lon: float
    swell_min_m: float
    swell_dir_range: Tuple[int, int]  # degrees
    preferred_wind_wave_max_m: float = 0.6  # optional, default
    facing_direction_deg: int  # e.g. 270 for west-facing

SPOTS: List[SurfSpot] = [
    SurfSpot(name="Fistral Beach", lat=50.4157, lon=-5.0950, swell_min_m=1.0, swell_dir_range=(250, 310), facing_direction_deg=290),
    SurfSpot(name="Perranporth", lat=50.3454, lon=-5.1542, swell_min_m=1.0, swell_dir_range=(240, 300), facing_direction_deg=270),
    SurfSpot(name="Watergate Bay", lat=50.4372, lon=-5.0541, swell_min_m=1.0, swell_dir_range=(250, 310), facing_direction_deg=315),
    SurfSpot(name="Constantine Bay", lat=50.5382, lon=-5.0262, swell_min_m=1.2, swell_dir_range=(250, 310), facing_direction_deg=270),
    SurfSpot(name="Polzeath", lat=50.5752, lon=-4.9137, swell_min_m=1.2, swell_dir_range=(270, 330), facing_direction_deg=180),
    SurfSpot(name="Sennen Cove", lat=50.0772, lon=-5.7005, swell_min_m=1.0, swell_dir_range=(250, 320), facing_direction_deg=315),
    SurfSpot(name="Praa Sands", lat=50.1004, lon=-5.3875, swell_min_m=1.2, swell_dir_range=(180, 240), facing_direction_deg=225),
    SurfSpot(name="Widemouth Bay", lat=50.7777, lon=-4.5567, swell_min_m=1.0, swell_dir_range=(250, 310), facing_direction_deg=270),
    SurfSpot(name="Croyde", lat=51.1287, lon=-4.2396, swell_min_m=1.2, swell_dir_range=(240, 290), facing_direction_deg=270),
    SurfSpot(name="Saunton Sands", lat=51.0702, lon=-4.2291, swell_min_m=1.0, swell_dir_range=(240, 290), facing_direction_deg=270),
]


