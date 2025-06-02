from fastapi import APIRouter
from typing import List, Dict
from datetime import datetime

from fastapi.responses import StreamingResponse
from app.spots import SPOTS, SurfSpot
from app.forecast import get_forecast, scrape_surf_forecast
from app.heuristics import evaluate_surfability
import io
import csv
from io import StringIO

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
        
        #print(f"Forecast is a list with {len(forecast)} items.")
        #if forecast:print("First forecast item:", forecast[0].dict())

        spot_debug = {
            "spot": spot.name,
            "forecasts": [],
        }

        surf_forecast=scrape_surf_forecast(spot.surf_forecast_url)  # Ensure we scrape the latest data
        for entry in surf_forecast[:15]:print("surf_forecast entry",entry)

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



def map_our_score_to_rating(score: str) -> int:
    if score == "Poor":
        return 0
    elif score == "Fair":
        return 1
    elif score == "Good":
        return 3
    elif score == "Excellent":
        return 5
    return -1  # fallback

def generate_forecast_comparison(spot: SurfSpot, our_forecast, surf_forecast) -> List[Dict]:
    surf_forecast_by_time = {
        datetime.fromisoformat(entry["datetime"]): entry
        for entry in surf_forecast
    }

    comparison_results = []
    for i, f in enumerate(our_forecast):
        try:
            # Convert string to datetime if needed
            time_obj = datetime.fromisoformat(f.time) if isinstance(f.time, str) else f.time
            our_time = time_obj.replace(minute=0, second=0, microsecond=0)
        except Exception as e:
            print(f"[WARN] Skipping forecast entry due to invalid time format: {f.time}, error: {e}")
            continue

        surf_entry = surf_forecast_by_time.get(our_time)

        if surf_entry:
            is_surfable, score, reason = evaluate_surfability(spot, our_forecast, i)
            our_rating = map_our_score_to_rating(score)
            surf_rating = int(surf_entry["rating"])

            # Only keep reason if we did *not* mark it surfable
            if is_surfable:
                justification_text = reason
                reason_text = ""
            else:
                reason_text = reason
                justification_text = ""
            

            match = (
                (our_rating == 0 and surf_rating == 0) or
                (our_rating == 1 and surf_rating in [1, 2]) or
                (our_rating == 3 and surf_rating in [3, 4]) or
                (our_rating == 5 and surf_rating >= 5)
            )

            comparison_results.append({
                "datetime": our_time.isoformat(),
                "our_score": score,
                "our_rating": our_rating,
                "surf_forecast_rating": surf_rating,
                "match": match,
                "reason": reason_text,
                "justification": justification_text
            })

    return comparison_results

@router.get("/compare-forecasts")
async def compare_forecasts():
    all_results = []

    for spot in SPOTS:
        if not spot.surf_forecast_url:
            continue

        print(f"[INFO] Processing spot: {spot.name}")
        surf_forecast = scrape_surf_forecast(spot.surf_forecast_url)
        our_forecast = await get_forecast(spot)
        comparison = generate_forecast_comparison(spot, our_forecast, surf_forecast)

        all_results.append({
            "spot": spot.name,
            "comparison": comparison
        })

    return {"results": all_results}



@router.get("/compare-forecasts-csv")
async def compare_forecasts():
    all_results = []
    comparison_rows = []

    for spot in SPOTS:
        if not spot.surf_forecast_url:
            continue

        print(f"[INFO] Processing spot: {spot.name}")
        try:
            surf_forecast = scrape_surf_forecast(spot.surf_forecast_url)
        except Exception as e:
            print(f"[WARN] Failed to scrape {spot.name}: {e}")
            continue  # skip this spot and continue with others

        try:
            our_forecast = await get_forecast(spot)
            comparison = generate_forecast_comparison(spot, our_forecast, surf_forecast)
        except Exception as e:
            print(f"[WARN] Failed to generate forecast for {spot.name}: {e}")
            continue

        all_results.append({
            "spot": spot.name,
            "comparison": comparison
        })

        # Add to CSV rows
        for row in comparison:
            row["spot"] = spot.name
            comparison_rows.append(row)

    # Prepare CSV
    if not comparison_rows:
        return {"error": "No comparison data available"}

    fieldnames = ["spot", "datetime", "our_score", "our_rating", "surf_forecast_rating", "match", "reason","justification"]
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(comparison_rows)
    output.seek(0)

    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=forecast_comparison.csv"})
