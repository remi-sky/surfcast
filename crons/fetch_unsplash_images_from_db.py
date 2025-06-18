import os
import asyncio
import asyncpg
import requests
from math import radians, cos, sin, sqrt, atan2
from dotenv import load_dotenv

# Load env vars
load_dotenv()

SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# Easily adjustable range
X = 1   # start index (inclusive)
Y = 10  # end index (exclusive)


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def fetch_spot_image(spot_name, lat=None, lon=None):
    query = f"{spot_name} surf UK"
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": query,
        "client_id": UNSPLASH_ACCESS_KEY,
        "per_page": 10
    }

    print(f"[INFO] Searching Unsplash for: {query}")

    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        print(f"[DEBUG] Got {len(results)} image results for '{spot_name}'")

        for idx, result in enumerate(results):
            loc = result.get("location", {})
            loc_name = loc.get("name", "").lower()
            pos = loc.get("position", {})

            print(f"[DEBUG] Result {idx}: location name = '{loc_name}', position = {pos}, url = {result['urls'].get('regular')}")

            if spot_name.lower() in loc_name:
                print(f"[INFO] Match on name for {spot_name}")
                return result["urls"]["regular"], f"{result['user']['name']} on Unsplash"

            if lat and lon and pos.get("latitude") and pos.get("longitude"):
                d = haversine_distance(lat, lon, pos["latitude"], pos["longitude"])
                print(f"[DEBUG] Distance to photo: {d:.2f} km")
                if d < 5:
                    print(f"[INFO] Match on coordinates for {spot_name} (distance: {d:.2f} km)")
                    return result["urls"]["regular"], f"{result['user']['name']} on Unsplash"

        print(f"[WARN] No suitable image found for {spot_name}")
        return None, None

    except Exception as e:
        print(f"[ERROR] Unsplash fetch failed for {spot_name}: {e}")
        return None, None


async def run():
    print("[INFO] Connecting to database...")
    conn = await asyncpg.connect(SUPABASE_DB_URL)

    query = """
        SELECT id, name, lat, lon
        FROM surf_spots
        Where surf_spots.name IN ('Croyde', 'Porthcawl', 'Perranporth', 'Polzeath', 'Fistral', 'Porthleven', 'Porthcurno', 'Porthtowan', 'Gwithian')
        ORDER BY name
        OFFSET $1 LIMIT $2
    """
    print(f"[INFO] Fetching surf spots from DB (offset {X}, limit {Y - X})")
    rows = await conn.fetch(query, X, Y - X)

    for row in rows:
        name = row["name"]
        lat = row["lat"]
        lon = row["lon"]
        print(f"\n[INFO] Processing spot: {name} ({lat}, {lon})")
        image_url, credit = fetch_spot_image(name, lat, lon)
        if image_url:
            print(f"[RESULT] {name}, {image_url}, {credit}")
        else:
            print(f"[RESULT] {name}, No suitable image found.")

    await conn.close()
    print("[INFO] Done.")


if __name__ == "__main__":
    asyncio.run(run())
