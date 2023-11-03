from flask import Flask, url_for, render_template, request, redirect
import requests, os
from pprint import pprint
from datetime import datetime



app = Flask(__name__)


@app.route('/')
def home():
    return  render_template('index.html', locations=locations)


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
        if self.location in locations:
            self.latitude = locations[self.location]['lat']
            self.altitude = locations[self.location]['alt']
            
        else:
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



locations = {
    'Lake District National Park': {
        'id': 'cumbria',
        'name': 'Lake District National Park',
        'lat': 54.4609,
        'alt': -3.0886
    },
    'the_cotswolds':{
        'id': 'the_cotswolds',
        'name': 'The Cotswolds',
        'lat': 50.6395,
        'alt': -2.0566
    },
    'cambridge':{
        'id': 'cambridge',
        'name': 'Cambridge ',
        'lat': 52.2053,
        'alt': 0.1218
    },
    'bristol':{
        'id': 'bristol',
        'name': 'Bristol',
        'lat': 51.4545,
        'alt': -2.5879
    },
    'oxford':{
        'id': 'oxford',
        'name': 'Oxford',
        'lat': 51.7520,
        'alt': -1.2577
    },
    'norwich':{
        'id': 'norwich',
        'name': 'Norwich',
        'lat': 52.6309,
        'alt': 1.2974
    },
    'stonehenge':{
        'id': 'stonehenge',
        'name': 'Stonehenge',
        'lat': 51.1789,
        'alt': -1.8262
    },
    'watergate_bay':{
        'id': 'watergate_bay',
        'name': 'Watergate Bay',
        'lat': 50.4429,
        'alt': -5.0553
    },
    'birmingham':{
        'id': 'birmingham',
        'name': 'Birmingham',
        'lat': 52.4862,
        'alt': -1.8904
    }
    
}


if __name__ == "__main__":
    app.run(debug=True)