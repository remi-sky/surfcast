# forecast.py
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from app.models import MarineForecast
from app.spots import SurfSpot
import requests
from bs4 import BeautifulSoup
from timezonefinder import TimezoneFinder



timeout = httpx.Timeout(10.0, connect=5.0)
retries = 2


async def fetch_with_retry(url, params, label, spot_name):
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except (httpx.ConnectTimeout, httpx.ReadTimeout,
                httpx.ConnectError, httpx.NetworkError,
                BrokenPipeError, ConnectionResetError) as e:
            print(f"[WARNING] Network issue fetching {label} (attempt {attempt + 1}/{retries}) for spot {spot_name}: {e}")
            if attempt == retries:
                return None
            await asyncio.sleep(1.5)
        except httpx.HTTPStatusError as e:
            print(f"[ERROR] HTTP error fetching {label} for {spot_name}: {e.response.status_code} {e.response.text}")
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error fetching {label} for {spot_name}: {e}")
            return None


async def get_forecast(
    spot: SurfSpot,
    timezone_str: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[MarineForecast]:

    if not start_date:
        start_date = datetime.utcnow().date().isoformat()
    if not end_date:
        end_date = (datetime.utcnow().date() + timedelta(days=14)).isoformat()

    marine_url = "https://marine-api.open-meteo.com/v1/marine"
    weather_url = "https://api.open-meteo.com/v1/forecast"

    marine_params = {
        "latitude": spot.lat,
        "longitude": spot.lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": [
            "wave_height", "wave_direction", "wave_period",
            "wind_wave_height", "wind_wave_period"
        ],
        "timezone": timezone_str,
    }

    weather_params = {
        "latitude": spot.lat,
        "longitude": spot.lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ["wind_speed_10m", "wind_direction_10m"],
        "timezone": timezone_str,
    }

    marine_data = await fetch_with_retry(marine_url, marine_params, "marine forecast", spot.name)
    weather_data = await fetch_with_retry(weather_url, weather_params, "weather forecast", spot.name)

    if not marine_data or not weather_data:
        print(f"[ERROR] Missing data for {spot.name}, skipping...")
        return []

    marine_hourly = {k: v for k, v in marine_data.get("hourly", {}).items()}
    weather_hourly = {k: v for k, v in weather_data.get("hourly", {}).items()}

    # Check critical keys before continuing
    required_keys = [
        "time", "wave_height", "wave_direction", "wave_period",
        "wind_wave_height", "wind_speed_10m", "wind_direction_10m"
    ]
    for key in required_keys:
        source = marine_hourly if key not in ["wind_speed_10m", "wind_direction_10m"] else weather_hourly
        if key not in source:
            print(f"[WARNING] Missing key '{key}' in Open-Meteo response for spot {spot.name}")
            return []

    forecasts = []
    times = marine_hourly["time"]
    for i, t in enumerate(times):
        try:
            forecast = MarineForecast(
                time=t,
                wave_height_m=marine_hourly["wave_height"][i],
                wave_direction_deg=marine_hourly["wave_direction"][i],
                wave_period_s=marine_hourly["wave_period"][i],
                wind_wave_height_m=marine_hourly["wind_wave_height"][i],
                wind_wave_period_s=marine_hourly.get("wind_wave_period", [None] * len(times))[i],
                wind_speed_kmh=weather_hourly["wind_speed_10m"][i],
                wind_direction_deg=weather_hourly["wind_direction_10m"][i],
            )
            forecasts.append(forecast)
        except Exception as e:
            print(f"[WARNING] Skipping index {i} for {spot.name} due to error: {e}")
            continue

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


