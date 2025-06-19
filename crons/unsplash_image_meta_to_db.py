import os
import csv
import asyncio
import asyncpg
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[WARNING] variable not loaded from .env, environment variables will only load from prod environment")



SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
CSV_PATH = "spots_images.csv"  # Path to your CSV file


def extract_photo_id(unsplash_url: str) -> str:
    parts = unsplash_url.rstrip("/").split("-")
    return parts[-1]


def fetch_image_metadata(photo_id: str):
    api_url = f"https://api.unsplash.com/photos/{photo_id}"
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
    
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        return {
            "image_url": data["urls"]["regular"],
            "credit_text": f'Photo by {data["user"]["name"]} on Unsplash',
            "credit_url": f'{data["user"]["links"]["html"]}?utm_source=your_app_name&utm_medium=referral',
            "source_url": data["links"]["html"]
        }
    except Exception as e:
        print(f"[ERROR] Failed to fetch metadata for photo_id={photo_id}: {e}")
        return None


async def update_db():
    conn = await asyncpg.connect(SUPABASE_DB_URL)

    with open(CSV_PATH, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            spot_name = row["spot_name"]
            unsplash_url = row["unsplash_page_url"]
            photo_id = extract_photo_id(unsplash_url)
            meta = fetch_image_metadata(photo_id)

            if not meta:
                print(f"[WARN] Skipping {spot_name} due to missing metadata")
                continue

            print(f"[INFO] Updating {spot_name} with image {meta['image_url']}")

            await conn.execute(
                """
                UPDATE surf_spots
                SET
                    image_url = $1,
                    image_credit = $2,
                    image_credit_url = $3,
                    image_source_url = $4
                WHERE name = $5
                """,
                meta["image_url"],
                meta["credit_text"],
                meta["credit_url"],
                meta["source_url"],
                spot_name,
            )

    await conn.close()
    print("[DONE] All spots processed.")


if __name__ == "__main__":
    asyncio.run(update_db())
