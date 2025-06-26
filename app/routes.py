from fastapi import APIRouter, Query, HTTPException, Path
from typing import List, Dict
from datetime import datetime, timedelta, date

from fastapi.responses import StreamingResponse
from app.spots import SurfSpot
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

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[WARNING] variable not loaded from .env, environment variables will only load from prod environment")


router = APIRouter()

DATABASE_URL = os.getenv("SUPABASE_DB_URL")
tf = TimezoneFinder()

# Rating priority for sorting
rating_priority = {"Firing": 4, "Solid": 3, "Playable": 2, "Sketchy": 1, "Lake Mode":0}

@router.get("/api/spots/forecasted")
async def get_forecasted_spots(
    lat: float,
    lon: float,
    max_distance_km: int = Query(100, ge=1, le=500)
):
    query = """
    SELECT
        s.id, s.name, s.lat, s.lon, s.region, s.town, s.surf_benchmark_url,
        f.timestamp_utc, f.surf_rating, f.explanation, f.swell_wave_height, f.swell_wave_peak_period, f.wind_speed_kmh, f.wind_type, f.wind_severity, f.swell_wave_direction
    FROM surf_spots s
    JOIN surf_forecast_hourly f ON f.spot_id = s.id
    WHERE ST_DWithin(
        s.geom,
        ST_SetSRID(ST_MakePoint($1, $2), 4326),
        $3 * 1000
    )
    AND f.timestamp_utc >= (NOW() AT TIME ZONE 'UTC')::date
    AND f.surf_rating IN ('Firing', 'Solid', 'Playable')
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
                    "swell_wave_height": f["swell_wave_height"],
                    "swell_wave_peak_period": f["swell_wave_peak_period"],
                    "wind_speed_kmh": f["wind_speed_kmh"],
                    "wind_type": f["wind_type"],
                    "wind_severity": f["wind_severity"],
                    "swell_wave_direction": f["swell_wave_direction"],
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
               swell_wave_height, swell_wave_peak_period, swell_wave_direction,
               wind_speed_kmh, wind_direction_deg, wind_type,
               surf_rating, explanation, wind_wave_height_m, wind_severity
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
                swell_wave_height=r["swell_wave_height"],
                swell_wave_direction=r.get("swell_wave_direction"),
                wind_wave_height_m=r.get("wind_wave_height_m"),
                swell_wave_peak_period=r.get("swell_wave_peak_period"),
                wind_speed_kmh=r.get("wind_speed_kmh"),
                wind_direction_deg=r.get("wind_direction_deg"),
                wind_type=r.get("wind_type"),
                wind_severity=r.get("wind_severity"),
                explanation=r.get("explanation"),
                rating=r.get("surf_rating"),
            )
        )

    if not forecasts:
        raise HTTPException(status_code=404, detail="No future forecasts available")

    return forecasts


@router.get("/api/spots/{spot_id}")
async def get_spot_details(spot_id: UUID):
    query = """
        SELECT id, name, lat, lon, facing_direction, swell_min_m,
               swell_dir_min, swell_dir_max, preferred_wind_wave_max_m,
               best_swell_dir_label, best_wind_dir_label, post_code, town,
               region, surf_benchmark_url, image_url, image_credit, image_credit_url,
               image_source_url, timezone
        FROM surf_spots
        WHERE id = $1
    """

    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        row = await conn.fetchrow(query, spot_id)
    except Exception as e:
        print(f"[ERROR] Spot details query failed: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if conn:
            await conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Spot not found")

    return dict(row)