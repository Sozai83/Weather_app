from flask import Flask, url_for, render_template, request, redirect
import requests, os, json, threading
import concurrent.futures
from pprint import pprint
from datetime import datetime
from locations import locations
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from classes import Weather, Geocode, map_api_key


app = Flask(__name__)


@app.route('/')
def home():
    locations_list = list(locations)

    def get_weather(location):
            geo_code = Geocode(location)
            geo_code.check_geocode()
            weather = Weather(location, geo_code.latitude, geo_code.longitude)
            weather.check_weather()
            
            return (weather.icon_small,geo_code.latitude,geo_code.longitude)

    markers=[]
    with concurrent.futures.ThreadPoolExecutor() as executor:
        get_weather_result = executor.map(get_weather, locations_list)
        for weather in get_weather_result:
            icon, lat, lng = weather
            markers.append(f'markers=icon:{icon}|{lat},{lng}')

    gmap = f"""
    https://maps.googleapis.com/maps/api/staticmap?center=Manchester,UK&zoom=6&size=1200x600
    &style=visibility:on&style=feature:water|element:geometry|visibility:on
    &style=feature:landscape|element:geometry|visibility:on
    &{'&'.join(markers)}
    &key={map_api_key}
    """

    return  render_template('index.html', locations=locations, gmap=gmap)


# Check weather for the selected location, and return data using weather.html template
@app.route('/checkweather', methods=['POST'])
def check_weather():
    if request.method == 'POST':
        try:
            location = request.form['location']
            unit = request.form['unit']

            # Create a Geocode object
            geo_code = Geocode(location)
            # Call check_geocode to retrieve latitude and longitude 
            geo_code.check_geocode()

            if geo_code.latitude and geo_code.longitude:
                # Create a Weather object
                weather = Weather(location, geo_code.latitude, geo_code.longitude,unit)

                # calsls the check_weather funcion to check current weather and store the data in the object 
                weather.check_weather()

                # calsls the check_weather_forecast function to check weather in the location for next 8 days and store the data in the object
                weather.check_weather_forecast()


                return render_template('weather.html', 
                                    location = location,
                                    weather = weather.weather,
                                    temp = weather.temp,
                                    temp_max = weather.temp_max,
                                    temp_min = weather.temp_min,
                                    humidity = weather.humidity,
                                    icon = weather.icon,
                                    date = weather.date,
                                    unit = weather.unit,
                                    next_7days = weather.weather_next_7days,
                                    latitude = weather.latitude,
                                    longitude = weather.longitude,
                                    map= weather.map
                                    )
            # If the geocode cannot be found, return the error page
            else:
                return redirect(url_for('error'))
        # If an error occurs, return the error page
        except:
            return redirect(url_for('error'))
        

@app.route('/error/')
def error():
    return render_template('error.html')


if __name__ == "__main__":
    app.run(debug=True)