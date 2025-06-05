# forecast.py

import httpx
from datetime import datetime, timedelta
from typing import List, Optional

from app.models import MarineForecast
from app.spots import SurfSpot


import requests
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
from datetime import datetime, timedelta
from timezonefinder import TimezoneFinder

async def get_forecast(spot: SurfSpot, timezone_str: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[MarineForecast]:
    if not start_date:
        start_date = datetime.utcnow().date().isoformat()
    if not end_date:
        end_date = (datetime.utcnow().date() + timedelta(days=13)).isoformat()

    marine_url = "https://marine-api.open-meteo.com/v1/marine"
    weather_url = "https://api.open-meteo.com/v1/forecast"

    common_params = {
        "latitude": spot.lat,
        "longitude": spot.lon,
        "start_date": start_date,
        "end_date": end_date,
        "timezone": timezone_str
    }
    print("DEBUG common_params:", common_params)

    marine_params = httpx.QueryParams({
        **common_params,
        "hourly": ",".join([
            "wave_height",
            "wave_direction",
            "wave_period",
            "wind_wave_height",
            "wind_wave_direction",
            "wind_wave_period",
        ])
    })

    weather_params = httpx.QueryParams({
        **common_params,
        "hourly": "wind_speed_10m,wind_direction_10m"
    })

    async with httpx.AsyncClient() as client:
        #print("DEBUG full marine request URL:", f"{marine_url}?{marine_params}")
        #print("DEBUG full weather request URL:", f"{weather_url}?{weather_params}")

        marine_response = await client.get(marine_url, params=marine_params)
        weather_response = await client.get(weather_url, params=weather_params)

        marine_response.raise_for_status()
        weather_response.raise_for_status()

        marine_data = marine_response.json()
        weather_data = weather_response.json()

        #print("Marine Status Code:", marine_response.status_code)
        #print("Weather Status Code:", weather_response.status_code)

        #print("Marine response JSON keys:", marine_data.keys())
        #print("Weather response JSON keys:", weather_data.keys())

    marine_hourly = marine_data.get("hourly", {})
    weather_hourly = weather_data.get("hourly", {})

    time = marine_hourly.get("time", [])
    #print("Available marine hourly keys:", list(marine_hourly.keys()))
    #for key, values in marine_hourly.items():
     #   print(f"{key}: {len(values)} values")

    #print("Available weather hourly keys:", list(weather_hourly.keys()))
    #for key, values in weather_hourly.items():
     #   print(f"{key}: {len(values)} values")

    #print("DEBUG time keys:", time)

    required_keys = [
        "wave_height", "wave_direction", "wind_wave_height", "wind_wave_direction",
        "wind_wave_period", "wave_period", "wind_speed_10m", "wind_direction_10m"
    ]
    min_length = min(
        len(marine_hourly.get(k, [])) if "wind_speed" not in k else len(weather_hourly.get(k, []))
        for k in required_keys
    )
    #print("Minimum length across all required hourly keys:", min_length)
    #print("Length of time:", len(time))

    forecasts = []

    for i in range(len(time)):
        try:
            forecast_data = {
                "time": time[i],
                "wave_height_m": marine_hourly.get("wave_height", [None])[i],
                "wave_direction_deg": marine_hourly.get("wave_direction", [None])[i],
                "wave_period_s": marine_hourly.get("wave_period", [None])[i],
                "wind_wave_height_m": marine_hourly.get("wind_wave_height", [None])[i],
                "wind_wave_direction_deg": marine_hourly.get("wind_wave_direction", [None])[i],
                "wind_wave_period_s": marine_hourly.get("wind_wave_period", [None])[i],
                "wind_speed_kmh": weather_hourly.get("wind_speed_10m", [None])[i],
                "wind_direction_deg": weather_hourly.get("wind_direction_10m", [None])[i],
            }

            forecasts.append(MarineForecast(**forecast_data))

        except (IndexError, ValueError, TypeError) as e:
            print(f"Skipping index {i} due to error: {e}")
            continue

    if forecasts:
        print(f"Received {len(forecasts)} forecast entries.")
        print("First forecast (as dict):", forecasts[0].dict())
    else:
        print("Forecast is empty.")

    return forecasts


def scrape_surf_forecast(url: str):
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        raise Exception(f"Failed to fetch URL {url} - Status Code: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")

    def extract_row(row_name):
        row = soup.find("tr", {"data-row-name": row_name})
        if not row:
            print(f"[WARN] Row '{row_name}' not found")
            return []
        values = [
            " ".join(cell.stripped_strings)
            for cell in row.find_all("td", class_="forecast-table__cell")
        ]
        print(f"[INFO] Extracted {len(values)} entries for '{row_name}'")
        return values

    times = extract_row("time")
    ratings = extract_row("rating")
    heights = extract_row("wave-height")
    periods = extract_row("periods")
    winds = extract_row("wind-state")

    # Extract date headers and map them to time slots
    date_cells = soup.select("td.js-fctable-day")
    print(f"[DEBUG] Found {len(date_cells)} day header cells")

    column_to_date = {}
    current_col = 0
    today = datetime.today()
    for cell in date_cells:
        try:
            day_text = cell.get("data-day-name", "").strip()
            if "_" in day_text:
                _, day = day_text.split("_")
                date = datetime(today.year, today.month, int(day))
                colspan = int(cell.get("colspan", "1"))
                for _ in range(colspan):
                    column_to_date[current_col] = date
                    current_col += 1
        except Exception as e:
            print(f"[WARN] Could not parse day from cell: {cell}")
            continue

    print(f"[INFO] Mapped {len(column_to_date)} columns to dates")

    min_len = min(len(times), len(ratings), len(heights), len(periods), len(winds))
    print(f"[INFO] Preparing {min_len} forecast entries")
    forecast = []
    for i in range(min_len):
        # Parse hour from time string
        time_str = times[i]
        try:
            # Try parsing formats like "10 AM" or "1 PM"
            parsed_time = datetime.strptime(time_str.strip(), "%I %p")
            hour = parsed_time.hour
        except ValueError:
            try:
                parsed_time = datetime.strptime(time_str.strip(), "%H:%M")
                hour = parsed_time.hour
            except ValueError:
                print(f"[WARN] Could not parse hour from time '{time_str}'")
                hour = 0

        date = column_to_date.get(i)
        if not date:
            print(f"[WARN] No date found for index {i}")
            continue

        dt = datetime(date.year, date.month, date.day, hour)
        forecast.append({
            "datetime": dt.isoformat(),
            "rating": ratings[i],
            "wave_height": heights[i],
            "wave_period": periods[i],
            "wind": winds[i],
        })

    return forecast


# Sample matching function for ratings
def map_our_rating_to_range(score: str) -> tuple:
    mapping = {
        "Poor": (0,),
        "Fair": (1, 2),
        "Good": (3, 4),
        "Excellent": tuple(range(5, 11))
    }
    return mapping.get(score, ())


