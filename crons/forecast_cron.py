#forecast_cron.py
import os
import sys
import asyncio
from datetime import datetime
import time
from typing import Optional
import json

import pytz
from timezonefinder import TimezoneFinder
from supabase import create_client, Client

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import MarineForecast, SurfForecast
from app.spots import SurfSpot, fetch_all_spots
from app.forecast import get_forecast
from app.heuristics import evaluate_surf_quality



try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[WARNING] variable not loaded from .env, environment variables will only load from prod environment")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
tf = TimezoneFinder()

async def process_spot(spot, spot_id: str):

    local_tz = pytz.timezone(spot.timezone)
    if not local_tz:
        print(f"[WARNING] No local timezone found for {spot.name}, skipping")
        return

    print (f"[DEBUG] Processing spot: {spot.name} (ID: {spot_id})")
    print(f"[DEBUG] Local timezone for {spot.name}: {local_tz.zone}")
    forecasts = await get_forecast(spot,spot.timezone, start_date=None, end_date=None)
 
    print(f"[DEBUG] {spot.name} → {len(forecasts)} total valid forecasts from Open-Meteo")
  
    relevant_hours = [6, 9, 12, 18, 21]
    rows = []
    for f in forecasts:
        try:
            local_dt = datetime.strptime(f.time, "%Y-%m-%dT%H:%M")
            if local_dt.hour not in relevant_hours:
                continue
            utc_dt = local_tz.localize(local_dt).astimezone(pytz.utc)
            print(f"[DEBUG] Processing forecast for {spot.name} at {local_dt.isoformat()} (UTC: {utc_dt.isoformat()})") 
            surf_forecast = evaluate_surf_quality(spot, f)

            rows.append({
                "spot_id": spot_id,
                "timestamp_local": local_dt.isoformat(),
                "timestamp_utc": utc_dt.isoformat(),
                "date_local": local_dt.date().isoformat(),
                "swell_wave_height": f.swell_wave_height,
                "swell_wave_direction": f.swell_wave_direction,
                "swell_wave_peak_period": f.swell_wave_peak_period,
                "wind_speed_kmh": f.wind_speed_kmh,
                "wind_direction_deg": f.wind_direction_deg,
                "wind_wave_height_m": f.wind_wave_height_m,
                "wind_type": surf_forecast.wind_type,
                "wind_severity": surf_forecast.wind_severity,
                "surf_rating": surf_forecast.rating,
                "explanation": surf_forecast.explanation,
            })
        except Exception as e:
            print(f"[ERROR] Parsing forecast for {spot.name}: {e}")

    

    print(f"[DEBUG] {spot.name} → {len(rows)} rows after filtering by relevant hours")

    for row in rows:
        try:
            #print(f"[DEBUG] Attempting upsert for spot: {spot.name}")
            #print(f"[DEBUG] Row content: {json.dumps(row, default=str, indent=2)}")
            #print(f"[DEBUG] Conflict keys: ['spot_id', 'timestamp_local']")
            assert "spot_id" in row and row["spot_id"], f"Missing or null spot_id in row: {row}"
            assert "timestamp_local" in row and row["timestamp_local"], f"Missing or null timestamp_local in row: {row}"
            response = supabase.table("surf_forecast_hourly").upsert(
                row, on_conflict="spot_id,timestamp_local"
            ).execute()

            #print(f"[SUCCESS] Upsert response: {response}")
        except Exception as e:
            print(f"[ERROR] Upsert failed for {spot.name}: {e}")


async def main():
    # ⏱ Start the timer
    start_time = time.time()
    total_forecasts_inserted = 0
    spots_processed = 0

    spots = await fetch_all_spots()

    for spot in spots:
        await process_spot(spot, str(spot.id))
        await asyncio.sleep(1)
    
    # ⏱ End the timer
    end_time = time.time()
    duration_sec = end_time - start_time

    print(f"\n[SUMMARY]")
    #print(f"Processed {spots_processed} spots")
    #print(f"Inserted {total_forecasts_inserted} forecast rows")
    print(f"Took {duration_sec:.2f} seconds total (~{duration_sec/60:.2f} minutes)")

if __name__ == "__main__":
    asyncio.run(main())

