#!/usr/bin/env python3
import os
import asyncio

import asyncpg
from timezonefinder import TimezoneFinder
from dotenv import load_dotenv

# Load DATABASE_URL from .env (optional)
load_dotenv()

DATABASE_URL = os.getenv("SUPABASE_DB_URL")
if not DATABASE_URL:
    raise RuntimeError("Please set SUPABASE_DB_URL in environment")

tf = TimezoneFinder()


async def backfill_timezones():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Fetch all spots (or only those without timezone)
        rows = await conn.fetch("""
            SELECT id, lat, lon
            FROM surf_spots
            WHERE timezone IS NULL
        """)
        print(f"Found {len(rows)} spots to update…")

        for record in rows:
            spot_id = record["id"]
            lat = record["lat"]
            lon = record["lon"]
            try:
                tz_name = tf.timezone_at(lat=lat, lng=lon) or "UTC"
            except Exception as e:
                print(f"  [!] Could not find timezone for spot {spot_id}: {e}")
                tz_name = "UTC"

            # Update the row
            await conn.execute(
                """
                UPDATE surf_spots
                SET timezone = $1
                WHERE id = $2
                """,
                tz_name,
                spot_id,
            )
            print(f"  ✓ Spot {spot_id} → {tz_name}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(backfill_timezones())
