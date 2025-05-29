from app.spots import SurfSpot
from app.forecast import MarineForecast

def evaluate_surfability(spot: SurfSpot, forecast: list[MarineForecast], index: int) -> tuple[bool, str, str]:
    try:
        f = forecast[index]
        wave_height = f.wave_height_m
        wave_direction = f.wave_direction_deg
        wind_wave_height = f.wind_wave_height_m
        wind_direction = f.wind_wave_direction_deg
        swell_period = f.wave_period_s
        wind_speed = f.wind_speed_kmh

        height_ok = wave_height is not None and wave_height >= spot.swell_min_m
        dir_ok = wave_direction is not None and spot.swell_dir_range[0] <= wave_direction <= spot.swell_dir_range[1]
        chop_ok = wind_wave_height is not None and wind_wave_height <= spot.preferred_wind_wave_max_m
        period_ok = swell_period is not None and swell_period >= 7

        wind_type = wind_quality(spot.facing_direction_deg, wind_direction) if wind_direction is not None else "unknown"
        wind_strength_ok = wind_speed is None or wind_type != "onshore" or wind_speed <= 15

        surf_level = classify_surf_level(wave_height, swell_period, wind_type, wind_wave_height, spot, wind_speed)

        if height_ok and dir_ok and chop_ok and period_ok and wind_strength_ok:
            return True, surf_level, None
        else:
            reason = []
            if not height_ok:
                reason.append(f"wave too small ({wave_height:.2f}m < {spot.swell_min_m}m)" if wave_height is not None else "missing wave height")
            if not dir_ok:
                reason.append(f"bad swell direction ({wave_direction}°)" if wave_direction is not None else "missing swell direction")
            if not chop_ok:
                reason.append(f"too choppy ({wind_wave_height:.2f}m)" if wind_wave_height is not None else "missing wind wave height")
            if not period_ok:
                reason.append(f"swell too weak ({swell_period}s)" if swell_period is not None else "missing swell period")
            if not wind_strength_ok:
                reason.append(f"strong onshore wind ({wind_speed} km/h)")

            return False, surf_level, "; ".join(reason)

    except Exception as e:
        print(f"Surfability evaluation error at index {index} for spot {spot.name}: {e}")
        return False, "Poor", "missing or invalid data"


def wind_quality(facing_deg: int, wind_deg: int) -> str:
    # Angle difference between where spot faces and wind comes from
    delta = (wind_deg - facing_deg + 360) % 360

    if 120 <= delta <= 240:
        return "offshore"
    elif 60 <= delta < 120 or 240 < delta <= 300:
        return "cross-shore"
    else:
        return "onshore"


def classify_surf_level(wave_height, swell_period, wind_type, wind_wave_height, spot: SurfSpot, wind_speed_kmh: float = 0) -> str:
    if wave_height < spot.swell_min_m or swell_period < 7:
        return "Poor"

    if wind_type == "onshore" and (wind_wave_height > spot.preferred_wind_wave_max_m or wind_speed_kmh > 15):
        return "Poor"

    if wave_height > spot.swell_min_m and swell_period >= 8:
        if wind_type == "offshore":
            return "Excellent"
        elif wind_type == "cross-shore":
            return "Good"
        else:
            return "Fair"

    return "Fair"
