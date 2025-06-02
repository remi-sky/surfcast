
import asyncio
import csv
from datetime import datetime
from typing import List
from app.forecast import get_forecast
from app.spots import SurfSpot, SPOTS  

output_file = "forecast_availability_check.csv"

async def check_forecast(spot: SurfSpot):
    try:
        forecast = await get_forecast(spot)
        success = len(forecast) > 0
        return {
            "spot_name": spot.name,
            "lat": spot.lat,
            "lon": spot.lon,
            "success": success,
            "error_message": "" if success else "No forecast returned",
            "wave_height": forecast[0].wave_height_m if success and forecast else None
        }
    except Exception as e:
        return {
            "spot_name": spot.name,
            "lat": spot.lat,
            "lon": spot.lon,
            "success": False,
            "error_message": str(e)
        }

async def main():
    results = []
    for spot in SPOTS:
        result = await check_forecast(spot)
        results.append(result)
        await asyncio.sleep(1.2)  # Wait 2 seconds between each request

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["spot_name", "lat", "lon", "success", "error_message","wave_height"])
        writer.writeheader()
        writer.writerows(results)

if __name__ == "__main__":
    asyncio.run(main())
