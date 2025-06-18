from fastapi import APIRouter, Query, HTTPException, Path
from typing import List, Dict
from datetime import datetime, timedelta, date

from fastapi.responses import StreamingResponse
from app.spots import SPOTS, SurfSpot
from app.forecast import get_forecast, scrape_surf_forecast
from io import StringIO
import os
from urllib.parse import urlparse
from supabase import create_client
import asyncpg
from collections import defaultdict
import pytz
from timezonefinder import TimezoneFinder
from app.models import SurfForecast
from uuid import UUID

from dotenv import load_dotenv
# Load env vars
load_dotenv()

router = APIRouter()

DATABASE_URL = os.getenv("SUPABASE_DB_URL")
tf = TimezoneFinder()

# Rating priority for sorting
rating_priority = {"Excellent": 3, "Good": 2, "Fair": 1, "Poor": 0}

@router.get("/api/spots/forecasted")
async def get_forecasted_spots(
    lat: float,
    lon: float,
    max_distance_km: int = Query(100, ge=1, le=500)
):
    query = """
    SELECT
        s.id, s.name, s.lat, s.lon, s.region, s.town, s.surf_benchmark_url,
        f.timestamp_utc, f.surf_rating, f.explanation
    FROM surf_spots s
    JOIN surf_forecast_hourly f ON f.spot_id = s.id
    WHERE ST_DWithin(
        s.geom,
        ST_SetSRID(ST_MakePoint($1, $2), 4326),
        $3 * 1000
    )
    AND f.timestamp_utc >= NOW()::date
    AND f.surf_rating IN ('Fair', 'Good', 'Excellent')
    ORDER BY s.id, f.timestamp_utc
    """

    try:
        conn = await asyncpg.connect(DATABASE_URL)
        rows = await conn.fetch(query, lon, lat, max_distance_km)
        await conn.close()
    except Exception as e:
        print(f"[ERROR] Forecast query failed: {e}")
        return {"error": str(e)}

    # Group rows by spot ID
    grouped = defaultdict(list)
    spot_info = {}
    for row in rows:
        spot_id = row["id"]
        grouped[spot_id].append(row)
        if spot_id not in spot_info:
            spot_info[spot_id] = {
                "id": spot_id,
                "name": row["name"],
                "lat": row["lat"],
                "lon": row["lon"],
                "region": row["region"],
                "town": row["town"],
                "surf_benchmark_url": row["surf_benchmark_url"]
            }

    # Find best forecast per day per spot (local time)
    output = []
    for spot_id, forecasts in grouped.items():
        tz_str = tf.timezone_at(lat=spot_info[spot_id]["lat"], lng=spot_info[spot_id]["lon"]) or "UTC"
        tz = pytz.timezone(tz_str)

        daily_best = {}
        for f in forecasts:
            dt_utc = f["timestamp_utc"]
            dt_local = dt_utc.replace(tzinfo=pytz.utc).astimezone(tz)
            day_str = dt_local.date().isoformat()
            current_best = daily_best.get(day_str)

            if not current_best or rating_priority[f["surf_rating"]] > rating_priority[current_best["rating"]]:
                daily_best[day_str] = {
                    "date": day_str,
                    "time": dt_local.strftime("%H:%M"),
                    "rating": f["surf_rating"],
                    "explanation": f["explanation"],
                    "timestamp_sort": dt_local
                }

        if daily_best:
            sorted_daily = sorted(daily_best.values(), key=lambda d: d["timestamp_sort"])
            spot_entry = spot_info[spot_id]
            spot_entry["forecasts"] = [
                {k: v for k, v in d.items() if k != "timestamp_sort"} for d in sorted_daily
            ]
            output.append(spot_entry)

    # Sort all spots by their soonest forecast timestamp
    output.sort(key=lambda s: s["forecasts"][0]["date"] + s["forecasts"][0]["time"])

    return output


@router.get(
    "/api/spots/{spot_id}/forecasts",
    response_model=list[SurfForecast],
    summary="Get detailed hourly forecasts for a specific spot (future only)"
)
async def get_spot_forecasts(
    spot_id: UUID = Path(..., description="UUID of the surf spot"),
    days: int = Query(10, ge=1, le=30, description="Number of days ahead to fetch")
):
    # 1) Load spot info, including its IANA time zone and coords
    lookup_sql = """
        SELECT lat, lon, timezone
        FROM surf_spots
        WHERE id = $1
    """
    conn = await asyncpg.connect(DATABASE_URL)
    spot = await conn.fetchrow(lookup_sql, spot_id)
    if not spot:
        await conn.close()
        raise HTTPException(status_code=404, detail="Spot not found")

    lat, lon, tz_name = spot["lat"], spot["lon"], spot["timezone"] or "UTC"
    tz = pytz.timezone(tz_name)

    # 2) Determine "now" in local time zone
    now_local = datetime.now(tz)

    # 3) Define date window
    start_date = now_local.date()
    end_date = start_date + timedelta(days=days)

    # 4) Fetch rows in date window (using timestamp_local for filtering by date)
    sql = """
        SELECT timestamp_utc, timestamp_local, date_local,
               wave_height_m, wave_period_s, wave_direction_deg,
               wind_speed_kmh, wind_direction_deg, wind_type,
               surf_rating, explanation, wind_wave_height_m
        FROM surf_forecast_hourly
        WHERE spot_id = $1
          AND timestamp_local::date BETWEEN $2 AND $3
        ORDER BY timestamp_utc
    """
    try:
        rows = await conn.fetch(sql, spot_id, start_date, end_date)
    finally:
        await conn.close()

    # 5) Filter future entries and map to SurfForecast
    forecasts = []
    for r in rows:
        # convert UTC timestamp to aware local time
        dt_utc = r["timestamp_utc"].replace(tzinfo=pytz.utc)
        dt_local = dt_utc.astimezone(tz)
        if dt_local < now_local:
            continue
        forecasts.append(
            SurfForecast(
                time=dt_local.isoformat(),
                timezone=tz_name,
                wave_height_m=r["wave_height_m"],
                wave_direction_deg=r.get("wave_direction_deg"),
                wind_wave_height_m=r.get("wind_wave_height_m"),
                wave_period_s=r.get("wave_period_s"),
                wind_speed_kmh=r.get("wind_speed_kmh"),
                wind_direction_deg=r.get("wind_direction_deg"),
                wind_type=r.get("wind_type"),
                explanation=r.get("explanation"),
                rating=r.get("surf_rating"),
            )
        )

    if not forecasts:
        raise HTTPException(status_code=404, detail="No future forecasts available")

    return forecasts