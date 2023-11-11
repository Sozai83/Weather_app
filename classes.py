from flask import Flask, url_for, render_template, request, redirect, jsonify
import requests, os, json, threading, asyncio
import concurrent.futures
from datetime import datetime
from locations import locations


# API Key for geocode_url
geocode_api_key = os.environ.get('GoogleMapAPIKey')
# API Key for map_url
map_api_key = os.environ.get('GoogleMapAPIKeyLimited')
# API Key for weather_url and weather_forecast_url
weather_api_key = os.environ.get('OpenWeather_API_key')


# Google map API - Retrieve longitude and latitude based on location
geocode_url = 'https://maps.googleapis.com/maps/api/geocode/json?address='
# Google map API - Embed map API URL
map_url = 'https://www.google.com/maps/embed/v1/place'
# Open Weather API - 
weather_url = 'https://api.openweathermap.org/data/3.0/onecall'



class Geocode:
    def __init__(self, location):
        self.location = location        

    def check_geocode(self):
        # If the location is in the existing location disctiornary, return latitude and longitude
        if self.location in locations:
            self.latitude = locations[self.location]['lat']
            self.longitude = locations[self.location]['lng']

            return self.latitude, self.longitude
        
        # Otherwise, retrieve latitude and longitude using google geocode API
        else:
            resp = requests.get(f'{geocode_url}{self.location.replace(" ", "+")}&key={geocode_api_key}')
            status = resp.json()['status']

            if resp.status_code == 200 and status != 'ZERO_RESULTS':
                self.latitude = resp.json()['results'][0]['geometry']['location']['lat']
                self.longitude = resp.json()['results'][0]['geometry']['location']['lng']
                
                return self.latitude, self.longitude

            else:
                raise Exception(f'Filed to retrieve geocode. Please try again. Error:{resp.status_code}')
        


class Weather:
    def __init__(self, latitude, longitude, unit='metric'):
        self.latitude = latitude
        self.longitude = longitude
        self.unit = unit

    def generate_map(self):
        self.map = f'{map_url}?key={map_api_key}&q={self.latitude},{self.longitude}&zoom=7'
        return self.map
    
    # Get current weather for the location
    def check_weather(self):
        resp = requests.get(f'{weather_url}?lat={self.latitude}&lon={self.longitude}&units={self.unit}&exclude=hourly,minutely,alerts&appid={weather_api_key}')
        
        if resp.status_code == 200:
            resp_json = resp.json()
            weather_forecast = resp_json['daily']
            cur_weather = resp_json['current']
            todays_weather = weather_forecast[0]

            self.weather = cur_weather['weather'][0]['main']
            self.humidity = cur_weather['humidity']
            self.temp = cur_weather['temp']
            self.temp_min = todays_weather['temp']['min']
            self.temp_max = todays_weather['temp']['max']
            self.icon = f"https://openweathermap.org/img/wn/{cur_weather['weather'][0]['icon']}@2x.png"
            self.icon_small = f"https://openweathermap.org/img/wn/{cur_weather['weather'][0]['icon']}.png"
            self.date = datetime.utcfromtimestamp(cur_weather['dt']).strftime('%Y/%m/%d %I%p')

            # Get weather forecast for next 8 days for the location and filtering the data
            weather_next_7days = map(lambda x: 
                {
                    'date': datetime.utcfromtimestamp(x['dt']).strftime('%m/%d'), 
                    'temp_min': x['temp']['min'],
                    'temp_max': x['temp']['max'],
                    'weather': x['weather'][0]['main'],
                    'icon': f"https://openweathermap.org/img/wn/{x['weather'][0]['icon']}.png"
                } 
                ,weather_forecast[1:])
            
            self.weather_next_7days = list(weather_next_7days)

            return self.weather,self.temp, self.temp_max, self.temp_min, self.humidity, self.icon, self.icon_small, self.date, self.weather_next_7days
        else:
            raise Excption (f'Filed to retrieve current weather. Please try again. Error:{resp.status_code}')



def get_map_with_weather(locations):
        # Function to return latitude, longitude and the weather icon
    def get_weather_map_items(location):
            geo_code = Geocode(location)
            latitude, longitude = geo_code.check_geocode()
            weather = Weather(latitude, longitude)
            weather.check_weather()
            
            return (weather.icon_small,latitude,longitude)

    markers=[]
    # Create threads to excute get_weather_map_items asyncronically for each location
    with concurrent.futures.ThreadPoolExecutor() as executor:
        get_weather_result = executor.map(get_weather_map_items, locations)

        # Add markers for each location
        for weather in get_weather_result:
            icon, lat, lng = weather
            markers.append(f'markers=icon:{icon}|{lat},{lng}')


    # Google Map Static API - Create a map image containing weatehr icons for each location 
    gmap = f"""
    https://maps.googleapis.com/maps/api/staticmap?center=Manchester,UK&zoom=6&size=1200x600
    &style=visibility:on&style=feature:water|element:geometry|visibility:on
    &style=feature:landscape|element:geometry|visibility:on
    &{'&'.join(markers)}
    &key={map_api_key}
    """
    return gmap
