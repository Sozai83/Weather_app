from flask import Flask, url_for, render_template, request, redirect, jsonify
import requests, os, json, threading
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
weather_url = 'https://api.openweathermap.org/data/2.5/weather'
weather_forecast_url = 'https://api.openweathermap.org/data/3.0/onecall'



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
                return  jsonify(message=f'Filed to retrieve geocode. Please try again. Error:{resp.status_code}', status=resp.status_code)
        


class Weather:
    def __init__(self, location, latitude, longitude, unit='metric'):
        self.location = location
        self.latitude = latitude
        self.longitude = longitude
        self.unit = unit
        self.map = f'{map_url}?key={map_api_key}&q={self.latitude},{self.longitude}'
    
    # Get current weather for the location
    def check_weather(self):
        resp = requests.get(f'{weather_url}?lat={self.latitude}&lon={self.longitude}&units={self.unit}&zoom=0&appid={weather_api_key}')
        
        if resp.status_code == 200:
            resp_json = resp.json()
            self.weather = resp_json['weather'][0]['main']
            self.temp = resp_json['main']['temp']
            self.temp_max = resp_json['main']['temp_max']
            self.temp_min = resp_json['main']['temp_min']
            self.humidity = resp_json['main']['humidity']
            self.icon = f"https://openweathermap.org/img/wn/{resp_json['weather'][0]['icon']}@2x.png"
            self.icon_small = f"https://openweathermap.org/img/wn/{resp_json['weather'][0]['icon']}.png"
            self.date = datetime.utcfromtimestamp(resp_json["dt"]).strftime('%Y/%m/%d %I%p')

            return (self.weather,self.temp, self.temp_max, self.temp_min, self.humidity, self.icon, self.icon_small, self.date)
        else:
            return jsonify(message=f'Filed to retrieve current weather. Please try again. Error:{resp.status_code}', status=resp.status_code)

    # Get weather forecast for next 8 days for the location
    def check_weather_forecast(self):
        resp = requests.get(f'{weather_forecast_url}?lat={self.latitude}&lon={self.longitude}&units={self.unit}&exclude=hourly,current,minutely,alerts&appid={weather_api_key}')
        
        if resp.status_code == 200:
            weather_next_7days = map(lambda x: 
                                    {
                                        'date': datetime.utcfromtimestamp(x['dt']).strftime('%m/%d'), 
                                        'temp_min': x['temp']['min'],
                                        'temp_max': x['temp']['max'],
                                        'weather': x['weather'][0]['main'],
                                        'icon': f"https://openweathermap.org/img/wn/{x['weather'][0]['icon']}.png"
                                    } 
                                    ,resp.json()['daily'][1:])
            self.weather_next_7days = list(weather_next_7days)

            return self.weather_next_7days
            
        else:
            return  jsonify(message=f'Filed to retrieve weather forecast data. Please try again. Error:{resp.status_code}', status=resp.status_code)