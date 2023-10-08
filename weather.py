import requests, json
from decouple import config

waipi = config('WAIPI')

def get_weather(city):
    r = requests.get(f'http://api.openweathermap.org/data/2.5/weather?appid={waipi}&q={city}&units=metric')
    weather = r.json()
    if 'Nothing to geocode' in weather.values():
        return False
    else:
        return weather