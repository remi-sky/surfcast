from supabase import create_client, Client
from app.spots import SPOTS
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("SUPABASE_URL:", SUPABASE_URL)
print("SUPABASE_KEY:", SUPABASE_KEY[:5] + "..." if SUPABASE_KEY else "None")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_spots():
    print
    for spot in SPOTS:
        data = {
            "name": spot.name,
            "lat": spot.lat,
            "lon": spot.lon,
            "facing_direction": spot.facing_direction_deg,
            "swell_min_m": spot.swell_min_m,
            "swell_dir_min": spot.swell_dir_range[0],
            "swell_dir_max": spot.swell_dir_range[1],
            "preferred_wind_wave_max_m": spot.preferred_wind_wave_max_m,
            "best_swell_dir_label": spot.best_swell_dir_label,
            "best_wind_dir_label": spot.best_wind_dir_label,
            "post_code": spot.postcode,
            "town": spot.town,
            "region": spot.region,
            "surf_benchmark_url": spot.surf_forecast_url,
        }

        try:
            response = supabase.table("surf_spots").insert(data).execute()

            if response.data is not None:
                print(f"[INFO] Inserted spot: {spot.name}")
            else:
                print(f"[WARN] Issue inserting {spot.name}: {response.error}")
        except Exception as e:
            print(f"[ERROR] Failed to insert {spot.name}: {e}")

if __name__ == "__main__":
    insert_spots()
    