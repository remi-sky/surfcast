# crons/delete_old_forecasts.py
import os
import asyncpg
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[WARNING] dotenv not installed, environment variables will only load from prod environment")


DATABASE_URL = os.getenv("SUPABASE_DB_URL")

async def run():
    conn = await asyncpg.connect(DATABASE_URL)
    deleted = await conn.execute("""
        DELETE FROM surf_forecast_hourly
        WHERE timestamp_utc < NOW()::date
    """)
    await conn.close()
    print(f"[CLEANUP] {deleted}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())