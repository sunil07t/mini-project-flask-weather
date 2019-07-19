# Error handling
from flask import Flask, render_template, redirect, request
import json, datetime, requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pandas.io.json import json_normalize 
import random

API_KEY = '026ac84477eb919f82c5876e9d764f82'
DIRECTION = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Load City list with ID and city name to get the id with city name
json.load(open('./city.list.json'))
cities_list = pd.read_json('city.list.json')

app = Flask(__name__)
 
@app.route('/')
def main():
    return redirect('/index')
 
 # Route of the main index page
@app.route('/index', methods = ['POST', 'GET'])
def index():
	info_list = []
	city_name = request.form.getlist('cityName')
	if(len(city_name) != 0):
		get_five_days_plot(city_name[0])
		info = get_current_weather(city_name[0])
		if(info != 'error'):
			info_list = make_info_list(info)
			app.logger.info(info_list[0])
		else:
			info_list.append(info)
	return render_template('index.html', info_list = info_list)

# Change degree to direction
def degreeToDirection(degree):
	index = int((degree / 45) + 0.5) % 8
	return DIRECTION[index]

# Make the info list that will be used on the template
def make_info_list(info):
	random_num = random.getrandbits(128)
	chart = 'static/img/forecast.png?' + str(random_num)
	icon = 'static/img/' + info['weather'][0]['icon'] + '.png'
	name = info['name'] + ", " + info['sys']['country']
	wind_direction = "Wind speed " + str(info['wind']['speed']) + ' m/h towards ' + degreeToDirection(info['wind']['deg'])
	info_list = [info['main']['temp'],
				info['main']['pressure'],
				info['main']['humidity'],
				name,
				chart,
				icon,
				wind_direction,
				info['coord']['lon'],
				info['coord']['lat']]
	return info_list

# Get the current weather with the city name
def get_current_weather(city):
	cities = cities_list[cities_list['name'] == city].reset_index()
	if(len(cities) != 0):
		city_id = cities.loc[0]['id']
		current = weather_forecast(city_id)
		app.logger.info('Current pass')
		return current
	else:
		app.logger.info('Current fail')
		return 'error'

# Get the forecast of next 5 days with the city name
def get_five_days_weather(city):
	cities = cities_list[cities_list['name'] == city].reset_index()
	if(len(cities) != 0):
		city_id = cities.loc[0]['id']
		forecast = weather_forecast(city_id, 'forecast')
		app.logger.info('forecast pass')
		return forecast
	else:
		app.logger.info('forecast fail')
		return 'error'

# Change date to be human readable
def make_date(dt_txt):
    date =  dt_txt.split(' ')[0]
    date_strip = date.split('-')
    date = datetime.date(int(date_strip[0]), int(date_strip[1]), int(date_strip[2]))
    day = date.strftime("%A")[:3] + "\n" + date.strftime("%B")[:3] + " " + date_strip[2]
    return day

# Get the temperature
def make_tempF_row(main):
    num = main['temp']
    return num

# Get the chart for the 5 days forecast
def get_five_days_plot(city):
	forecast = get_five_days_weather(city)
	if (forecast != 'error'):
		app.logger.info('about to save plot')
		forcast_plot_data = get_forcast_plot_data(forecast)
		plt.rcParams["figure.figsize"] = 11, 12
		plt.rcParams["xtick.labelsize"] = 10
		sns.set_context("poster")
		sns_plot = sns.factorplot('date', 'temperature (F)', data=forcast_plot_data, size=7)
		sns_plot.savefig("static/img/forecast.png")

# Get the data to input in the chart for the 5 days forecast
def get_forcast_plot_data(forecast):
	forcast_df = json_normalize(forecast, 'list')
	forcast_df['date'] = forcast_df['dt_txt'].apply(make_date)
	forcast_df['temperature (F)'] = forcast_df['main'].apply(make_tempF_row)
	forcast_df_to_plot = forcast_df.groupby(['date'], sort=False)['temperature (F)'].max().reset_index()
	return forcast_df_to_plot

# API wrapper to get either the current weather or the 5 days forecast from OpenWeatherMap
def weather_forecast(cityid, current = 'weather'):
    params = { 'id': cityid,
              'units': 'imperial',
               'APPID': API_KEY, 
             }
    res = requests.get('http://api.openweathermap.org/data/2.5/' + current, params=params)
    return res.json()

# route to 404
@app.errorhandler(404) 
def page_not_found(e):
    return render_template('404.html')
 
if __name__ == "__main__":
    app.run(debug=True)