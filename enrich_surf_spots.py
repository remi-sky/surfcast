import pandas as pd
import re
from typing import Tuple, Optional

# Mapping of cardinal directions to degrees
DIRECTION_TO_DEG = {
    "North": 0,
    "North-Northeast": 22,
    "Northeast": 45,
    "East-Northeast": 67,
    "East": 90,
    "East-Southeast": 112,
    "Southeast": 135,
    "South-Southeast": 157,
    "South": 180,
    "South-Southwest": 202,
    "Southwest": 225,
    "West-Southwest": 247,
    "West": 270,
    "West-Northwest": 292,
    "Northwest": 315,
    "North-Northwest": 337,
}

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates()

def extract_best_swell_direction(text: str) -> Optional[str]:
    match = re.search(r"when a\s*([A-Za-z\s-]+?)\s*swell", text, re.IGNORECASE)
    if match:
        return match.group(1).strip().title()
    return None

def extract_best_wind_direction(text: str) -> Optional[str]:
    match = re.search(r"from the\s*([A-Za-z\s-]+?)[\.\,]", text, re.IGNORECASE)
    if match:
        return match.group(1).strip().title()
    return None

def direction_to_deg(direction: Optional[str]) -> Optional[int]:
    if not direction:
        return None
    return DIRECTION_TO_DEG.get(direction.strip().title())

def compute_swell_dir_range(best_deg: Optional[int]) -> Optional[Tuple[int, int]]:
    if best_deg is None:
        return None
    return ((best_deg - 30) % 360, (best_deg + 30) % 360)

def compute_facing_deg(wind_deg: Optional[int]) -> Optional[int]:
    if wind_deg is None:
        return None
    return (wind_deg + 180) % 360

def generate_forecast_url(name: str) -> str:
    name_slug = name.strip().replace(" ", "-")
    return f"https://www.surf-forecast.com/breaks/{name_slug}/forecasts/latest"

def enrich_spots(csv_path: str, output_path: str):
    df = pd.read_csv(csv_path)
    df = remove_duplicates(df)

    swell_dirs = []
    wind_dirs = []
    swell_ranges = []
    facing_dirs = []
    forecast_urls = []
    swell_mins = []

    for _, row in df.iterrows():
        desc = row.get("Best surf description", "")
        name = row.get("Spot Name", "")

        swell_dir = extract_best_swell_direction(desc)
        wind_dir = extract_best_wind_direction(desc)
        swell_deg = direction_to_deg(swell_dir)
        wind_deg = direction_to_deg(wind_dir)

        swell_dirs.append(swell_dir)
        wind_dirs.append(wind_dir)
        swell_ranges.append(compute_swell_dir_range(swell_deg))
        facing_dirs.append(compute_facing_deg(wind_deg))
        forecast_urls.append(generate_forecast_url(name))
        swell_mins.append(1.0)  # Default for now

    df["Best swell direction"] = swell_dirs
    df["Best wind direction"] = wind_dirs
    df["Swell dir range"] = swell_ranges
    df["Facing direction deg"] = facing_dirs
    df["Swell min m"] = swell_mins
    df["Surf forecast URL"] = forecast_urls

    df.to_csv(output_path, index=False)
    print(f"[DONE] Enriched data saved to {output_path}")

if __name__ == "__main__":
    enrich_spots("./app/indonesia_surf_spots.csv", "./enriched_indonesia_surf_spots.csv")
