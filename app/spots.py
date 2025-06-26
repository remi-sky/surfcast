import asyncpg
import os
from typing import List
from typing import Optional
from pydantic import BaseModel
from uuid import UUID

class SurfSpot(BaseModel):
    id: UUID
    name: str
    lat: float
    lon: float
    facing_direction: Optional[float]
    swell_min_m: Optional[float]
    swell_dir_min: Optional[float]
    swell_dir_max: Optional[float]
    preferred_wind_wave_max_m: Optional[float]
    best_swell_dir_label: Optional[str]
    best_wind_dir_label: Optional[str]
    post_code: Optional[str]
    town: Optional[str]
    region: Optional[str]
    surf_benchmark_url: Optional[str]
    geom: Optional[str]  # Can use `str` or define your own GeoJSON model if needed
    image_url: Optional[str]
    image_credit: Optional[str]
    image_credit_url: Optional[str]
    image_source_url: Optional[str]
    timezone: Optional[str]

    @property
    def swell_dir_range(self) -> tuple[float, float]:
        return (self.swell_dir_min or 0.0, self.swell_dir_max or 360.0)

    @property
    def facing_direction_deg(self) -> float:
        return self.facing_direction or 0.0
    
# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[WARNING] variable not loaded from .env, environment variables will only load from prod environment")

DATABASE_URL = os.getenv("SUPABASE_DB_URL")

async def fetch_all_spots() -> List[SurfSpot]:
    query = """
    SELECT
        id, name, lat, lon, facing_direction, swell_min_m,
        swell_dir_min, swell_dir_max, preferred_wind_wave_max_m,
        best_swell_dir_label, best_wind_dir_label,
        post_code, town, region, surf_benchmark_url,
        geom, image_url, image_credit, image_credit_url, image_source_url,
        timezone
    FROM surf_spots
    """

    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch(query)
    await conn.close()

    spots = [SurfSpot(**dict(row)) for row in rows]
    print(f"[DEBUG] Loaded {len(spots)} surf spots from Supabase")
    return spots