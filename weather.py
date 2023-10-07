import requests, json

waipi = "982f6a34a97a2023cb183fafabb2407e"

def get_weather(city):
    r = requests.get(f'http://api.openweathermap.org/data/2.5/weather?appid={waipi}&q={city}&units=metric')
    weather = r.json()
    if 'Nothing to geocode' in weather.values():
        return False
    else:
        return weather