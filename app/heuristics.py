from typing import Tuple
from app.spots import SurfSpot
from app.models import MarineForecast
from app.models import SurfForecast

def fmt(value, unit="", decimals=2):
    if value is None:
        return "n/a"
    return f"{value:.{decimals}f}{unit}"

def wind_quality(facing_deg: int, wind_deg: int) -> str:
    delta = (wind_deg - facing_deg + 360) % 360
    if 120 <= delta <= 240:
        return "offshore"
    elif 60 <= delta < 120 or 240 < delta <= 300:
        return "cross-shore"
    else:
        return "onshore"

def evaluate_surf_quality(spot: SurfSpot, forecast: MarineForecast) -> SurfForecast:
    explanations = []

    wave_height = forecast.wave_height_m
    swell_period = forecast.wave_period_s
    wave_dir = forecast.wave_direction_deg
    wind_wave_height = forecast.wind_wave_height_m
    wind_speed = forecast.wind_speed_kmh
    wind_dir = forecast.wind_direction_deg

    wind_type = wind_quality(spot.facing_direction_deg, wind_dir) if wind_dir is not None else "unknown"

    # Default rating
    rating = "Fair"

    if wave_height is None or wave_height < spot.swell_min_m:
        explanations.append(f"Wave too small ({fmt(wave_height, 'm')} < {spot.swell_min_m}m)" if wave_height is not None else "Missing wave height")

    if wave_dir is None or not (spot.swell_dir_range[0] <= wave_dir <= spot.swell_dir_range[1]):
        explanations.append(f"Bad swell direction ({fmt(wave_dir, '°')} not in {spot.swell_dir_range})" if wave_dir is not None else "Missing swell direction")

    if wind_wave_height is None or wind_wave_height > spot.preferred_wind_wave_max_m:
        explanations.append(f"Too choppy (wind wave {fmt(wind_wave_height, 'm')})" if wind_wave_height is not None else "Missing wind wave height")

    if swell_period is None or swell_period < 7:
        explanations.append(f"Swell period too short ({fmt(swell_period, 's')} < 7s)" if swell_period is not None else "Missing swell period")

    if explanations:
        rating = "Poor"
        reason = "; ".join(explanations) + f" | wind_type={wind_type}"
    else:
        if wind_type == "offshore":
            if swell_period >= 12 and wave_height >= 1:
                rating = "Excellent"
                reason = f"Powerful swell and clean offshore wind ({fmt(wave_height, 'm')} @ {fmt(swell_period, 's')}, wind {fmt(wind_speed, 'km/h', 0)})"
            elif swell_period >= 8:
                rating = "Good"
                reason = f"Good swell and clean offshore wind ({fmt(wave_height, 'm')} @ {fmt(swell_period, 's')}, wind {fmt(wind_speed, 'km/h', 0)})"
            else:
                rating = "Fair"
                reason = f"Offshore wind with short period swell ({fmt(wave_height, 'm')} @ {fmt(swell_period, 's')}, wind {fmt(wind_speed, 'km/h', 0)})"
        elif wind_type == "cross-shore":
            if swell_period >= 11:
                if wind_speed and wind_speed > 25:
                    rating = "Good"
                    reason = f"Strong cross-shore wind ({fmt(wind_speed, 'km/h', 0)}) but long swell period ({fmt(swell_period, 's')})"
                else:
                    rating = "Good"
                    reason = f"Long swell period ({fmt(swell_period, 's')}) with cross-shore wind ({fmt(wind_speed, 'km/h', 0)})"
            elif swell_period >= 8:
                if wind_speed and wind_speed > 25:
                    rating = "Fair"
                    reason = f"Moderate swell with strong cross-shore wind ({fmt(wind_speed, 'km/h', 0)})"
                else:
                    rating = "Good"
                    reason = f"Decent swell ({fmt(swell_period, 's')}) and manageable cross-shore wind ({fmt(wind_speed, 'km/h', 0)})"
            else:
                rating = "Fair"
                reason = f"Short swell period ({fmt(swell_period, 's')}) with cross-shore wind ({fmt(wind_speed, 'km/h', 0)})"
        elif wind_type == "onshore":
            if wind_speed is not None and wind_speed < 8:
                rating = "Good"
                reason = f"Onshore wind but light ({fmt(wave_height, 'm')} @ {fmt(swell_period, 's')}, {fmt(wind_speed, 'km/h', 0)})"
            elif wind_speed is not None and wind_speed < 15:
                rating = "Fair"
                reason = f"Onshore wind but still manageable ({fmt(wave_height, 'm')} @ {fmt(swell_period, 's')}, {fmt(wind_speed, 'km/h', 0)})"
            else:
                rating = "Poor"
                reason = f"Choppy onshore wind ({fmt(wind_speed, 'km/h', 0)})"
        else:
            rating = "Fair"
            reason = f"Surfable conditions but wind direction is unknown ({fmt(wave_height, 'm')} @ {fmt(swell_period, 's')})"

    return SurfForecast(
        time=forecast.time,
        wave_height_m=wave_height,
        wave_direction_deg=wave_dir,
        wind_wave_height_m=wind_wave_height,
        wind_wave_period_s=forecast.wind_wave_period_s,
        wave_period_s=swell_period,
        wind_speed_kmh=wind_speed,
        wind_direction_deg=wind_dir,
        wind_type=wind_type,
        explanation=reason,
        rating=rating
    )
