import logging
import requests

logger = logging.getLogger(__name__)

FORECAST_URL = "https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&daily=weathercode,sunrise,sunset,temperature_2m_max,temperature_2m_min,wind_direction_10m_dominant,wind_speed_10m_max,wind_gusts_10m_max&hourly=precipitation,visibility&timezone=Europe%2FLondon&wind_speed_unit=mph"


def get_weather_data(lat, long):
    url = FORECAST_URL.format(lat=lat, long=long)
    response = requests.get(url)

    if not 200 <= response.status_code < 300:
        logging.error(f"Failed to retrieve forecast data: {response.content}")
        raise RuntimeError("Failed to retrieve forecast data.")
    
    return response.json()



def parse_daily_data(data):
    daily_data = {
        "time": data.get("daily", {}).get("time", []),
        "weathercode": data.get("daily", {}).get("weathercode", []),
        "temperature_2m_max": data.get("daily", {}).get("temperature_2m_max", []),
        "temperature_2m_min": data.get("daily", {}).get("temperature_2m_min", []),
        "sunrise": data.get("daily", {}).get("sunrise", []),
        "sunset": data.get("daily", {}).get("sunset", []),
        "wind_direction_10m_dominant": data.get("daily", {}).get("wind_direction_10m_dominant", []),
        "wind_speed_10m_max": data.get("daily", {}).get("wind_speed_10m_max", []),
        "wind_gusts_10m_max": data.get("daily", {}).get("wind_gusts_10m_max", []),
    }
    forecast_data = {}
    for index, day in enumerate(daily_data["time"]):
        forecast_data[day] = {
            "weathercode": daily_data["weathercode"][index],
            "weather_icon": map_weather_code_to_icon(daily_data["weathercode"][index], 1),
            "temperature_2m_max": daily_data["temperature_2m_max"][index],
            "temperature_2m_min": daily_data["temperature_2m_min"][index],
            "sunrise": daily_data["sunrise"][index].split("T")[1],
            "sunset": daily_data["sunset"][index].split("T")[1],
            "wind_direction_10m_dominant": daily_data["wind_direction_10m_dominant"][index],
            "wind_arrow": get_wind_arrow(daily_data["wind_direction_10m_dominant"][index]),
            "wind_speed_10m_max": daily_data["wind_speed_10m_max"][index],
            "wind_gusts_10m_max": daily_data["wind_gusts_10m_max"][index],
        }
    return forecast_data

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

def parse_hourly_data(data):
    hourly_data = {
        "time": data.get("hourly", {}).get("time", []),
        "precipitation": data.get("hourly", {}).get("precipitation", []),
        "visibility": data.get("hourly", {}).get("visibility", []),
    }
    time_splits = get_am_pm_index(hourly_data["time"])
    for date, indices in time_splits.items():
        morning_precipitation = hourly_data["precipitation"][indices["am_start"]:indices["am_end"] + 1]
        afternoon_precipitation = hourly_data["precipitation"][indices["pm_start"]:indices["pm_end"] + 1]
        am_mean_precipitation = round(sum(morning_precipitation) / len(morning_precipitation), 2) if morning_precipitation else 0
        pm_mean_precipitation = round(sum(afternoon_precipitation) / len(afternoon_precipitation), 2) if afternoon_precipitation else 0
        morning_visibility = hourly_data["visibility"][indices["am_start"]:indices["am_end"] + 1]
        afternoon_visibility = hourly_data["visibility"][indices["pm_start"]:indices["pm_end"] + 1]
        am_mean_visibility = round(sum(morning_visibility) / len(morning_visibility), 2) if morning_visibility else 0
        pm_mean_visibility = round(sum(afternoon_visibility) / len(afternoon_visibility), 2) if afternoon_visibility else 0
        hourly_data[date] = {
            "am_precipitation": am_mean_precipitation,
            "pm_precipitation": pm_mean_precipitation,
            "am_visibility": am_mean_visibility,
            "pm_visibility": pm_mean_visibility
        }
    return hourly_data

def get_weather_forecast(lat, long):
    data = get_weather_data(lat, long)
    daily_data = parse_daily_data(data)
    hourly_data = parse_hourly_data(data)

    forecast = {}

    for date in daily_data.keys():
        if date in hourly_data:
            forecast[date] = daily_data[date] | hourly_data[date]
    return forecast
    
def map_weather_code_to_icon(weather_code, is_day):

    icon = "01d" # Default to clear day icon
    
    if weather_code in [0]:   # Clear sky
        icon = "01d"
    elif weather_code in [1]: # Mainly clear
        icon = "022d"
    elif weather_code in [2]: # Partly cloudy
        icon = "02d"
    elif weather_code in [3]: # Overcast
        icon = "04d"
    elif weather_code in [51, 61, 80]: # Drizzle, showers, rain: Light
        icon = "51d"          
    elif weather_code in [53, 63, 81]: # Drizzle, showers, rain: Moderatr
        icon = "53d"
    elif weather_code in [55, 65, 82]: # Drizzle, showers, rain: Heavy
        icon = "09d"
    elif weather_code in [45]: # Fog
        icon = "50d"                       
    elif weather_code in [48]: # Icy fog
        icon = "48d"
    elif weather_code in [56, 66]: # Light freezing Drizzle
        icon = "56d"            
    elif weather_code in [57, 67]: # Freezing Drizzle
        icon = "57d"            
    elif weather_code in [71, 85]: # Snow fall: Slight
        icon = "71d"
    elif weather_code in [73]:     # Snow fall: Moderate
        icon = "73d"
    elif weather_code in [75, 86]: # Snow fall: Heavy
        icon = "13d"
    elif weather_code in [77]:     # Snow grain
        icon = "77d"
    elif weather_code in [95]: # Thunderstorm
        icon = "11d"
    elif weather_code in [96, 99]: # Thunderstorm with slight and heavy hail
        icon = "11d"

    if is_day == 0:
        if icon == "01d":
            icon = "01n"      # Clear sky night
        elif icon == "022d":
            icon = "022n"     # Mainly clear night
        elif icon == "02d":
            icon = "02n"      # Partly cloudy night                
        elif icon == "10d":
            icon = "10n"      # Rain night

    return icon


def get_wind_arrow(wind_deg: float) -> str:
    DIRECTIONS = [
        ("↓", 22.5),    # North (N)
        ("↙", 67.5),    # North-East (NE)
        ("←", 112.5),   # East (E)
        ("↖", 157.5),   # South-East (SE)
        ("↑", 202.5),   # South (S)
        ("↗", 247.5),   # South-West (SW)
        ("→", 292.5),   # West (W)
        ("↘", 337.5),   # North-West (NW)
        ("↓", 360.0)    # Wrap back to North
    ]
    wind_deg = wind_deg % 360
    for arrow, upper_bound in DIRECTIONS:
        if wind_deg < upper_bound:
            return arrow
    
    return "↑"

