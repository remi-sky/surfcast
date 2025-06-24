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

    if wind_speed is not None and wind_dir is not None:
        wind_type, wind_severity = wind_quality(spot.facing_direction_deg, wind_dir, wind_speed)
    else:
        wind_type, wind_severity = "unknown", "unknown"

    # Default rating
    rating = "Playable"

    # Handle invalid inputs and blocking issues
    if swell_wave_height is None or swell_wave_height < spot.swell_min_m:
        explanations.append(f"Swell too small ({fmt(swell_wave_height, 'm')} < {spot.swell_min_m}m)" if swell_wave_height is not None else "Missing wave height")

    if wave_dir is None or not (spot.swell_dir_range[0] <= wave_dir <= spot.swell_dir_range[1]):
        explanations.append(f"Bad swell direction ({fmt(wave_dir, '°')} not in {spot.swell_dir_range})" if wave_dir is not None else "Missing swell direction")

    if wind_wave_height is None or wind_wave_height > spot.preferred_wind_wave_max_m:
        explanations.append(f"Too choppy (wind wave {fmt(wind_wave_height, 'm')})" if wind_wave_height is not None else "Missing wind wave height")

    if swell_period is None or swell_period < 7:
        explanations.append(f"Swell period too short ({fmt(swell_period, 's')} < 7s)" if swell_period is not None else "Missing swell period")

    # Fallback if any critical value is invalid
    if explanations:
        rating = "Lake Mode"
        reason = "; ".join(explanations) + f" | wind_type={wind_type}, wind_severity={wind_severity}"

    else:
        # Wind-tolerant rating logic based on swell period and wind
        if swell_period >= 12:
            # Cleanest conditions — Firing
            if wind_type in ["offshore", "glassy"] and wind_speed <= 12:
                rating = "Firing"
                reason = f"Powerful long-period swell with clean/glassy wind ({fmt(swell_wave_height, 'm')} @ {fmt(swell_period, 's')}, wind: {wind_type})"

            # Still very good — Solid, slightly more wind
            elif wind_type == "offshore" and wind_speed <= 20:
                rating = "Solid"
                reason = f"Long-period swell with strong but manageable offshore wind ({fmt(wind_speed, 'km/h', 0)})"

            # Light onshore or cross-shore — still holding
            elif wind_type in ["onshore", "cross-shore"] and wind_speed < 8:
                rating = "Solid"
                reason = f"Strong swell handling light {wind_type} wind ({fmt(wind_speed, 'km/h', 0)})"

            # Moderate onshore/cross — degrading but surfable
            elif (wind_type == "onshore" and wind_speed < 12) or (wind_type == "cross-shore" and wind_speed < 15):
                rating = "Playable"
                reason = f"Long-period swell with degrading {wind_type} wind ({fmt(wind_speed, 'km/h', 0)})"

            # Anything else — too much wind
            else:
                rating = "Sketchy"
                reason = f"Strong swell but messy due to wind ({wind_type}, {fmt(wind_speed, 'km/h', 0)})"


        elif 10 <= swell_period < 12:
            # Ideal surface – Solid
            if wind_type in ["offshore", "glassy"] and wind_speed <= 15:
                rating = "Solid"
                reason = f"Solid swell with clean or favourable wind ({fmt(wind_speed, 'km/h', 0)} {wind_type})"

            # Light onshore or side-wind – Playable
            elif wind_type in ["onshore", "cross-shore"] and wind_speed < 8:
                rating = "Playable"
                reason = f"Good swell but slight texture from wind ({wind_type}, {fmt(wind_speed, 'km/h', 0)})"

            # Moderate cross-shore – still surfable
            elif wind_type == "cross-shore" and wind_speed < 12:
                rating = "Playable"
                reason = f"Decent swell with moderate cross-shore wind ({fmt(wind_speed, 'km/h', 0)})"

            # Otherwise – degraded
            else:
                rating = "Sketchy"
                reason = f"Solid swell potential but wind downgrading quality ({wind_type}, {fmt(wind_speed, 'km/h', 0)})"

        elif 7 <= swell_period < 10:
    
            # Clean or glassy wind – still fun
            if wind_type in ["offshore", "glassy"] and wind_speed <= 12:
                rating = "Playable"
                reason = f"Shorter-period swell but clean surface conditions ({wind_type}, {fmt(wind_speed, 'km/h', 0)})"

            # Very light onshore/cross-shore wind
            elif wind_type in ["onshore", "cross-shore"] and wind_speed < 6:
                rating = "Playable"
                reason = f"Weak swell but manageable wind ({wind_type}, {fmt(wind_speed, 'km/h', 0)})"

            # Light/moderate cross-shore only if swell is clean
            elif wind_type == "cross-shore" and wind_speed < 10:
                rating = "Sketchy"
                reason = f"Short-period swell with some cross-shore wind ({fmt(wind_speed, 'km/h', 0)})"

            # Everything else — wind overpowers this swell
            else:
                rating = "Lake Mode"
                reason = f"Low-period swell and wind ruining the surface ({wind_type}, {fmt(wind_speed, 'km/h', 0)})"

        else:
            rating = "Lake Mode"
            reason = f"Insufficient swell period ({fmt(swell_period, 's')})"

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

