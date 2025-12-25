
import requests
import logging
import os
import json

TIDE_URL = "https://admiraltyapi.azure-api.net/uktidalapi/api/V1/Stations/{location}/TidalEvents?duration={duration}"
STATION_URL = "https://admiraltyapi.azure-api.net/uktidalapi/api/V1/Stations/{location}"

def get_station_name(location, api_key):
    hdr ={
    # Request headers
    'Cache-Control': 'no-cache',
    'Ocp-Apim-Subscription-Key': api_key,
    }
    url = STATION_URL.format(location=location)
    response = requests.get(url, headers=hdr)

    if not 200 <= response.status_code < 300:
        logging.error(f"Failed to get station data: {response.content}")
        raise RuntimeError("Failed to retrieve station data.")
    
    data = response.content

    return json.loads(data)["properties"]["Name"]

def get_tide_data(location, duration, api_key):
    hdr ={
    # Request headers
    'Cache-Control': 'no-cache',
    'Ocp-Apim-Subscription-Key': api_key,
    }
    url = TIDE_URL.format(location=location, duration=duration)
    response = requests.get(url, headers=hdr)

    if not 200 <= response.status_code < 300:
        logging.error(f"Failed to get tide data: {response.content}")
        raise RuntimeError("Failed to retrieve tide data.")
    
    data = response.content

    return json.loads(data)

def parse_tide_data(data):
    tide_events = {}
    for event in data:
        event_date_time = event.get("DateTime")
        event_date = event_date_time.split("T")[0]
        if event_date not in tide_events:
            tide_events[event_date] = {"tides": []}
        event['Height'] = round(event.get("Height", 0), 2)
        event['Time'] = event_date_time.split("T")[1]
        event['EventType'] = event.get("EventType", "")[0]
        event.pop("DateTime", None)
        event.pop("Filtered", None)
        event.pop("IsApproximateTime", None)
        event.pop("IsApproximateHeight", None)
        tide_events[event_date]["tides"].append(event)
    return tide_events

def get_tide_forecast(location, duration, api_key):
    data = get_tide_data(location, duration, api_key)
    tides = parse_tide_data(data)
    return tides
