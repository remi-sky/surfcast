#forecast_cron.py
import os
import sys
import asyncio
from datetime import datetime
import time
from typing import Optional
import json

import pytz
#from dotenv import load_dotenv
from timezonefinder import TimezoneFinder
from supabase import create_client, Client

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.spots import SPOTS
from app.models import MarineForecast, SurfForecast
from app.forecast import get_forecast
from app.heuristics import evaluate_surf_quality

# Load env vars
#load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
tf = TimezoneFinder()

async def process_spot(spot, spot_id: str):
    tz_str = tf.timezone_at(lat=spot.lat, lng=spot.lon)
    if not tz_str:
        print(f"[WARNING] No timezone found for {spot.name}, skipping")
        return
    local_tz = pytz.timezone(tz_str)

    forecasts = await get_forecast(spot,tz_str, start_date=None, end_date=None)
 
  
    relevant_hours = [3, 6, 9, 12, 18, 21]
    rows = []
    for f in forecasts:
        try:
            local_dt = datetime.strptime(f.time, "%Y-%m-%dT%H:%M")
            if local_dt.hour not in relevant_hours:
                continue
            utc_dt = local_dt.replace(tzinfo=local_tz).astimezone(pytz.utc)
            surf_forecast = evaluate_surf_quality(spot, f)

            rows.append({
                "spot_id": spot_id,
                "timestamp_local": local_dt.isoformat(),
                "timestamp_utc": utc_dt.isoformat(),
                "date_local": local_dt.date().isoformat(),
                "wave_height_m": f.wave_height_m,
                "wave_direction_deg": f.wave_direction_deg,
                "wave_period_s": f.wave_period_s,
                "wind_speed_kmh": f.wind_speed_kmh,
                "wind_direction_deg": f.wind_direction_deg,
                "wind_wave_height_m": f.wind_wave_height_m,
                "wind_type": surf_forecast.wind_type,
                "surf_rating": surf_forecast.rating,
                "explanation": surf_forecast.explanation,
            })
        except Exception as e:
            print(f"[ERROR] Parsing forecast for {spot.name}: {e}")

    import json  # add this at the top if not already imported

    print(f"[INFO] Inserting {len(rows)} forecast rows for {spot.name}")
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

    # Get DB surf spots with ID
    result = supabase.table("surf_spots").select("id, name").execute()
    id_map = {r["name"]: r["id"] for r in result.data}

    for spot in SPOTS[:2]:
        spot_id = id_map.get(spot.name)
        if not spot_id:
            print(f"[WARNING] No spot_id found for {spot.name}")
            continue
        await process_spot(spot, spot_id)
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

