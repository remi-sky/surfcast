from typing import Tuple
from app.spots import SurfSpot
from app.models import MarineForecast
from app.models import SurfForecast

def fmt(value, unit="", decimals=2):
    if value is None:
        return "n/a"
    return f"{value:.{decimals}f}{unit}"

def wind_quality(facing_deg: int, wind_deg: int, wind_speed_kmh: float) -> str:
    if wind_speed_kmh < 3:
        return "glassy"
    delta = (wind_deg - facing_deg + 360) % 360
    if 120 <= delta <= 240:
        return "offshore"
    elif 60 <= delta < 120 or 240 < delta <= 300:
        return "cross-shore"
    else:
        return "onshore"
    

def wind_quality(facing_deg: int, wind_deg: int, wind_speed_kmh: float) -> Tuple[str, str]:
    # Severity thresholds (surf-focused, not Beaufort labels)
    if wind_speed_kmh < 3:
        return "glassy", "none"
    elif wind_speed_kmh <= 10:
        severity = "light"
    elif wind_speed_kmh <= 18:
        severity = "breezy"
    else:
        severity = "strong"

    # Direction logic
    delta = (wind_deg - facing_deg + 360) % 360
    if 120 <= delta <= 240:
        wind_type = "offshore"
    elif 60 <= delta < 120 or 240 < delta <= 300:
        wind_type = "cross-shore"
    else:
        wind_type = "onshore"

    return wind_type, severity

def evaluate_surf_quality(spot: SurfSpot, forecast: MarineForecast) -> SurfForecast:
    explanations = []

    swell_wave_height = forecast.swell_wave_height
    swell_period = forecast.swell_wave_peak_period
    wave_dir = forecast.swell_wave_direction
    wind_wave_height = forecast.wind_wave_height_m
    wind_speed = forecast.wind_speed_kmh
    wind_dir = forecast.wind_direction_deg

    # Get wind type and severity using updated function
    wind_type, wind_severity = wind_quality(spot.facing_direction, wind_dir, wind_speed) if wind_dir is not None else ("unknown", "unknown")

    # Check for basic issues
    if swell_wave_height is None or swell_wave_height < (spot.swell_min_m or 0.5):
        explanations.append(f"Swell too small ({fmt(swell_wave_height, 'm')} < {spot.swell_min_m or '0.5'}m)")

    if wave_dir is None or not (spot.swell_dir_range[0] <= wave_dir <= spot.swell_dir_range[1]):
        explanations.append(f"Bad swell direction ({fmt(wave_dir, '°')} not in {spot.swell_dir_range})")

    if wind_wave_height is None or wind_wave_height > (spot.preferred_wind_wave_max_m or 1.0):
        explanations.append(f"Too choppy (wind wave {fmt(wind_wave_height, 'm')})")

    if swell_period is None or swell_period < 7:
        explanations.append(f"Swell period too short ({fmt(swell_period, 's')} < 7s)")

    # If we have disqualifying conditions
    if explanations:
        rating = "Lake Mode"
        reason = "; ".join(explanations)
    else:
        # Heuristic logic — can be tweaked
        if swell_period >= 12:
            if wind_type in ["offshore", "glassy"] and wind_speed <= 12:
                rating = "Firing"
                reason = f"Powerful long-period swell with clean/glassy wind ({fmt(swell_wave_height, 'm')} @ {fmt(swell_period, 's')}, wind: {wind_type})"
            elif wind_type == "offshore" and wind_speed <= 18:
                rating = "Solid"
                reason = f"Long-period swell with manageable offshore wind ({fmt(swell_wave_height, 'm')} @ {fmt(swell_period, 's')}, wind: {wind_type})"
            elif wind_type in ["onshore", "cross-shore"] and wind_speed < 8:
                rating = "Solid"
                reason = f"Strong swell handling light onshore wind ({wind_type}, {fmt(wind_speed, 'km/h', 0)})"
            elif (wind_type == "onshore" and wind_speed < 12) or (wind_type == "cross-shore" and wind_speed < 15):
                rating = "Playable"
                reason = f"Long swell period with some wind degradation ({wind_type}, {fmt(wind_speed, 'km/h', 0)})"
            else:
                rating = "Sketchy"
                reason = f"Long swell but messy wind ({wind_type}, {fmt(wind_speed, 'km/h', 0)})"

        elif 10 <= swell_period < 12:
            if wind_type in ["offshore", "glassy"] and wind_speed <= 15:
                rating = "Solid"
                reason = f"Solid swell and favorable wind ({fmt(swell_period, 's')} and {wind_type})"
            elif wind_type == "onshore" and wind_speed < 8:
                rating = "Playable"
                reason = f"Decent swell with light onshore wind ({fmt(wind_speed, 'km/h', 0)})"
            else:
                rating = "Sketchy"
                reason = f"Decent swell but degraded by wind ({wind_type}, {fmt(wind_speed, 'km/h', 0)})"

        elif 8 <= swell_period < 10:
            if wind_type in ["offshore", "glassy"] and wind_speed <= 10:
                rating = "Playable"
                reason = f"Short-period swell made surfable by clean wind ({fmt(swell_period, 's')} / {wind_type})"
            else:
                rating = "Sketchy"
                reason = f"Short-period swell and imperfect wind ({wind_type}, {fmt(wind_speed, 'km/h', 0)})"

        else:
            rating = "Lake Mode"
            reason = f"Too weak or disorganized (swell {fmt(swell_wave_height, 'm')} @ {fmt(swell_period, 's')})"

    return SurfForecast(
        time=forecast.time,
        swell_wave_height=swell_wave_height,
        swell_wave_direction=wave_dir,
        wind_wave_height_m=wind_wave_height,
        swell_wave_peak_period=swell_period,
        wind_speed_kmh=wind_speed,
        wind_direction_deg=wind_dir,
        wind_type=wind_type,
        wind_severity=wind_severity,
        explanation=reason,
        rating=rating
    )


