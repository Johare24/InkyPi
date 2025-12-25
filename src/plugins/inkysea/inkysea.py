from plugins.base_plugin.base_plugin import BasePlugin
import logging
from datetime import datetime, date
import pytz

from .tide_forecast import get_tide_forecast, get_station_name
from .marine_forecast import get_marine_forecast
from .weather_forecast import get_weather_forecast


logger = logging.getLogger(__name__)


class InkySea(BasePlugin):
    def generate_settings_template(self):
        template_params = super().generate_settings_template()
        template_params['api_key'] = {
            "required": True,
            "service": "AdmiraltyTidalApi",
            "expected_key": "TIDAL_API_KEY"
        }
        template_params['style_settings'] = True
        return template_params

    def generate_image(self, settings, device_config):
        lat = float(settings.get('latitude'))
        long = float(settings.get('longitude'))
        tide_key = device_config.load_env_key("TIDAL_API_KEY")
        port_id = settings.get('portID')

        try:
            tide_data = get_tide_forecast(port_id, 7, tide_key)
            marine_data = get_marine_forecast(lat, long)
            weather_data = get_weather_forecast(lat, long)
            title = get_station_name(port_id, tide_key)
        except Exception as e:
            logger.error(f"Data request failed: {str(e)}")
            raise RuntimeError(f"Data request failure, please check logs.")

        if not lat or not long:
            raise RuntimeError("Latitude and Longitude are required.")
        
        template_params = {
            "forecast": []
        }
        for day in weather_data.keys():
            if day in tide_data and day in marine_data:
                day_name = date.fromisoformat(day).strftime("%a")
                
                template_params["forecast"].append({
                    "day": day_name,
                    "icon": self.get_plugin_dir(f'icons/{weather_data[day]["weather_icon"]}.png'),
                    "tides": tide_data[day]["tides"],
                    "weather": weather_data[day],
                    "marine": marine_data[day],
                })
        

        template_params['title'] = title

        timezone = device_config.get_config("timezone", default="Europe/London")
        time_format = device_config.get_config("time_format", default="24h")
        tz = pytz.timezone(timezone)

        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        template_params["plugin_settings"] = settings

        # Add last refresh time
        now = datetime.now(tz)
        if time_format == "24h":
            last_refresh_time = now.strftime("%Y-%m-%d %H:%M")
        else:
            last_refresh_time = now.strftime("%Y-%m-%d %I:%M %p")
        template_params["last_refresh_time"] = last_refresh_time
        print(template_params)
        image = self.render_image(dimensions, "inkysea.html", "inkysea.css", template_params)

        if not image:
            raise RuntimeError("Failed to take screenshot, please check logs.")
        return image


    

    
