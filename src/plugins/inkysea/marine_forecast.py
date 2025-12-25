import logging, requests

MARINE_FORECAST_URL = "https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={long}&hourly=wave_height,wave_direction,sea_level_height_msl&timezone=Europe%2FLondon"

def get_marine_data(lat, long):
    url = MARINE_FORECAST_URL.format(lat=lat, long=long)
    response = requests.get(url)

    if not 200 <= response.status_code < 300:
        logging.error(f"Failed to retrieve marine forecast data: {response.content}")
        raise RuntimeError("Failed to retrieve marine forecast data.")
    
    return response.json()

def get_sea_state_description(wave_height):
    if wave_height < 0.5:
        return "Smooth"
    elif 0.5 <= wave_height < 1.25:
        return "Slight"
    elif 1.25 <= wave_height < 2.5:
        return "Moderate"
    elif 2.5 <= wave_height < 4.0:
        return "Rough"
    elif 4.0 <= wave_height < 6.0:
        return "Very Rough"
    elif 6.0 <= wave_height < 9.0:
        return "High"
    elif 9.0 <= wave_height < 14.0:
        return "Very High"
    else:
        return "Phenomenal"

def get_am_pm_index(times):
    dates = {}
    for index, measurement_time in enumerate(times):
        date = measurement_time.split("T")[0]
        time = measurement_time.split("T")[1]
        if time == "00:00":
            dates[date] = {}
            dates[date]["am_start"] = index
        elif time == "11:00":
            dates[date]["am_end"] = index
        elif time == "12:00":
            dates[date]["pm_start"] = index
        elif time == "23:00":
            dates[date]["pm_end"] = index
    return dates

def parse_marine_forecast(data):
    marine_data = {
        "time": data.get("hourly", {}).get("time", []),
        "wave_height": data.get("hourly", {}).get("wave_height", []),
        "wave_direction": data.get("hourly", {}).get("wave_direction", []),
        "sea_level_height_msl": data.get("hourly", {}).get("sea_level_height_msl", []),
    }
    time_splits = get_am_pm_index(marine_data["time"])

    for date, indices in time_splits.items():
        morning_values = marine_data["wave_height"][indices["am_start"]:indices["am_end"] + 1]
        afternoon_values = marine_data["wave_height"][indices["pm_start"]:indices["pm_end"] + 1]
        morning_mean = round(sum(morning_values) / len(morning_values), 2) if morning_values else 0
        afternoon_mean = round(sum(afternoon_values) / len(afternoon_values), 2) if afternoon_values else 0
        marine_data[date] = {
            "am_mean_wave_height": morning_mean,
            "am_sea_state": get_sea_state_description(morning_mean),
            "pm_mean_wave_height": afternoon_mean,
            "pm_sea_state": get_sea_state_description(afternoon_mean)
        }
    return marine_data

def get_marine_forecast(lat, long):
    data = get_marine_data(lat, long)
    marine_data = parse_marine_forecast(data)
    return marine_data
