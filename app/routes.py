from fastapi import APIRouter
from app.spots import SPOTS
from app.forecast import get_forecast
from app.heuristics import evaluate_surfability

router = APIRouter()

@router.get("/surfable-spots")
async def get_surfable_spots():
    surfable_spots = []

    for spot in SPOTS:
        forecast = await get_forecast(spot)
        #print("Forecast keys:", forecast.keys())
        #print("First hour values:", {key: forecast["hourly"][key][0] for key in forecast["hourly"]})

        print(f"Forecast is a list with {len(forecast)} items.")
        if forecast:print("First forecast item:", forecast[0].dict())

        for i, hour_data in enumerate(forecast):
            is_surfable, score, reason = evaluate_surfability(spot, forecast, i)
            if is_surfable:
                surfable_spots.append({
                    "spot": spot.name,
                    "score": score,
                    "reason": reason,
                    "time": hour_data["time"],
                })
                break  # Stop after the first surfable time slot

    return {"surfable_spots": surfable_spots}



@router.get("/debug-surfability")
async def debug_surfability():
    all_forecasts = []

    for spot in SPOTS:
        forecast = await get_forecast(spot)
        #print("Forecast keys:", forecast.keys())
        #print("First hour values:", {key: forecast["hourly"][key][0] for key in forecast["hourly"]})
       
        print(f"Forecast is a list with {len(forecast)} items.")
        if forecast:print("First forecast item:", forecast[0].dict())

        spot_debug = {
            "spot": spot.name,
            "forecasts": [],
        }

        for i, hour_data in enumerate(forecast):
            is_surfable, score, reason = evaluate_surfability(spot, forecast, i)

            # Merge all available fields with decision info
            debug_entry = {
                "time": hour_data.time,
                "wave_height": hour_data.wave_height_m,
                "wave_period": hour_data.wave_period_s,
                "wave_direction": hour_data.wave_direction_deg,
                "wind_wave_height": hour_data.wind_wave_height_m,
                "wind_wave_direction": hour_data.wind_wave_direction_deg,
                "wind_wave_period": hour_data.wind_wave_period_s,
                "is_surfable": is_surfable,
                "score": score,
                "reason": reason,
            }

            spot_debug["forecasts"].append(debug_entry)

        all_forecasts.append(spot_debug)

    return {"spots": all_forecasts}