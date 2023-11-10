from flask import Flask, url_for, render_template, request, redirect
import requests, os, json, threading, asyncio
import concurrent.futures
from datetime import datetime
from locations import locations
from classes import Weather, Geocode, map_api_key

app = Flask(__name__)


@app.route('/')
@app.route('/home')
def home():
    locations_list = list(locations)

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
        get_weather_result = executor.map(get_weather_map_items, locations_list)

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

    return  render_template('index.html', locations=locations, gmap=gmap)


# Check weather for the selected location, and return data using weather.html template
@app.route('/checkweather', methods=['POST'])
def check_weather():

    try:
        location = request.form['location'] if request.form['location'] != 'Other' else request.form['location_other']
        unit = request.form['unit'] if request.form['unit'] else 'metric'

        # Create a Geocode object
        geo_code = Geocode(location)
        # Call check_geocode to retrieve latitude and longitude 
        latitude, longitude = geo_code.check_geocode()

        try:
            #Create a Weather object
            weather = Weather(latitude, longitude, unit)
            # calls the check_weather funcion to check current weather and store the data in the object
            cur_weather, temp, temp_max, temp_min, humidity, icon, icon_small, date, weather_next_7days = weather.check_weather()
            # Generate location map 
            map = weather.generate_map()

            return render_template('weather.html', 
                                    location = location,
                                    weather = cur_weather,
                                    temp = temp,
                                    temp_max = temp_max,
                                    temp_min = temp_min,
                                    humidity = humidity,
                                    icon = icon,
                                    date = date,
                                    unit = unit,
                                    next_7days = weather_next_7days,
                                    latitude = latitude,
                                    longitude = longitude,
                                    map= map
                                    )
        # If the geocode cannot be found, return the error page
        except:
            return redirect(url_for('error', error_msg='Location or weather failed to be retrieved. Please try again.'))
    # If an error occurs, return the error page
    except:
        return redirect(url_for('error', error_msg='Location was not selected or the location could not be found. Please try again.'))

        


@app.route('/error/<string:error_msg>')
def error(error_msg=''):
    return render_template('error.html', error_msg=error_msg)


if __name__ == "__main__":
    app.run(debug=True)