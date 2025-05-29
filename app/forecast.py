# forecast.py

import httpx
from datetime import datetime, timedelta
from typing import List, Optional

from app.models import MarineForecast
from app.spots import SurfSpot


async def get_forecast(spot: SurfSpot, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[MarineForecast]:
    if not start_date:
        start_date = datetime.utcnow().date().isoformat()
    if not end_date:
        end_date = (datetime.utcnow().date() + timedelta(days=2)).isoformat()

    marine_url = "https://marine-api.open-meteo.com/v1/marine"
    weather_url = "https://api.open-meteo.com/v1/forecast"

    common_params = {
        "latitude": spot.lat,
        "longitude": spot.lon,
        "start_date": start_date,
        "end_date": end_date,
        "timezone": "Europe/London"
    }

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
        print("DEBUG full marine request URL:", f"{marine_url}?{marine_params}")
        print("DEBUG full weather request URL:", f"{weather_url}?{weather_params}")

        marine_response = await client.get(marine_url, params=marine_params)
        weather_response = await client.get(weather_url, params=weather_params)

        marine_response.raise_for_status()
        weather_response.raise_for_status()

        marine_data = marine_response.json()
        weather_data = weather_response.json()

        print("Marine Status Code:", marine_response.status_code)
        print("Weather Status Code:", weather_response.status_code)

        print("Marine response JSON keys:", marine_data.keys())
        print("Weather response JSON keys:", weather_data.keys())

    marine_hourly = marine_data.get("hourly", {})
    weather_hourly = weather_data.get("hourly", {})

    time = marine_hourly.get("time", [])
    print("Available marine hourly keys:", list(marine_hourly.keys()))
    for key, values in marine_hourly.items():
        print(f"{key}: {len(values)} values")

    print("Available weather hourly keys:", list(weather_hourly.keys()))
    for key, values in weather_hourly.items():
        print(f"{key}: {len(values)} values")

    print("DEBUG time keys:", time)

    required_keys = [
        "wave_height", "wave_direction", "wind_wave_height", "wind_wave_direction",
        "wind_wave_period", "wave_period", "wind_speed_10m", "wind_direction_10m"
    ]
    min_length = min(
        len(marine_hourly.get(k, [])) if "wind_speed" not in k else len(weather_hourly.get(k, []))
        for k in required_keys
    )
    print("Minimum length across all required hourly keys:", min_length)
    print("Length of time:", len(time))

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
