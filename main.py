from flask import Flask, url_for, render_template, request, redirect
import requests, os
from pprint import pprint
from datetime import datetime



app = Flask(__name__)


@app.route('/')
def home():
    return  render_template('index.html')


@app.route('/checkweather', methods=['POST'])
def check_weather():
    if request.method == 'POST':
        location = request.form['location']
        geo_code = Geocode(location)
        geo_code.check_geocode()

        if geo_code.latitude and geo_code.altitude:
            weather = Weather(location, geo_code.latitude, geo_code.altitude)
            weather.check_weather()
            return render_template('weather.html', 
                                   weather = weather.weather,
                                   temp = weather.temp,
                                   temp_max = weather.temp_max,
                                   temp_min = weather.temp_min,
                                   humidity = weather.humidity,
                                   icon = weather.icon,
                                   date = weather.date,
                                   location = location
                                   )
        else:
            return 'Please select valid location'


geocode_api_key = os.environ.get('GoogleMapAPIKey')
weather_api_key = os.environ.get('OpenWeather_API_key')
geocode_url = 'https://maps.googleapis.com/maps/api/geocode/json?address='
weather_url = 'https://api.openweathermap.org/data/2.5/weather'


class Geocode:
    def __init__(self, location):
        self.location = location        

    def check_geocode(self):
        resp = requests.get(f'{geocode_url}{self.location.replace(" ", "+")}&key={geocode_api_key}')
        status = resp.json()['status']

        if resp.status_code == 200 and status != 'ZERO_RESULTS':
            self.latitude = resp.json()['results'][0]['geometry']['location']['lat']
            self.altitude = resp.json()['results'][0]['geometry']['location']['lng']
            print(self.latitude, self.altitude)
        else:
            print(status)
        


class Weather:
    def __init__(self, location, latitude, altitude):
        self.location = location
        self.latitude = latitude
        self.altitude = altitude
    
    def check_weather(self):
        resp = requests.get(f'{weather_url}?lat={self.latitude}&lon={self.altitude}&units=metric&appid={weather_api_key}')
        
        if resp.status_code == 200:
            resp_json = resp.json()
            self.weather = resp_json['weather'][0]['main']
            self.temp = resp_json['main']['temp']
            self.temp_max = resp_json['main']['temp_max']
            self.temp_min = resp_json['main']['temp_min']
            self.humidity = resp_json['main']['humidity']
            self.icon = f"https://openweathermap.org/img/wn/{resp_json['weather'][0]['icon']}@2x.png"
            self.date = datetime.utcfromtimestamp(resp_json["dt"]).strftime('%Y-%m-%d')
        else:
            print(resp.status_code)



if __name__ == "__main__":
    app.run(debug=True)