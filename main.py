import requests
from models import City,WeatherRecord
import json
import folium
import webbrowser
from decorators import validate_city
from concurrent.futures import ThreadPoolExecutor, as_completed

@validate_city
def get_coordinates(city):

    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"

    response = requests.get(url)
    data = response.json()

    if "results" not in data:
        raise ValueError("City not found!")

    result = data["results"][0]

    return City(
        city,
        result["latitude"],
        result["longitude"],
        result["country"]
    )


def get_weather_data(lat, long):
    weather_result = requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&current=temperature_2m,wind_speed_10m,weather_code"
    )

    weather_data = weather_result.json()

    current_weather = weather_data["current"]["temperature_2m"]
    current_wind = weather_data["current"]["wind_speed_10m"]
    current_code = weather_data["current"]["weather_code"]

    return WeatherRecord(current_weather, current_wind, current_code)


def save_weather(city_name, weather):

    with open("history.json", "r") as file:
        data = json.load(file)

    data.append({
        "city": city_name,
        "temperature": weather.temperature,
        "wind_speed": weather.wind_speed,
        "weather_code": weather.weather_code,
        "description": get_weather_description(weather.weather_code)
    })

    with open("history.json", "w") as file:
        json.dump(data, file, indent=4)




def show_history():

    with open("history.json", "r") as file:
        data = json.load(file)

    for item in data:
        print("-------------------")
        print(f"City: {item['city']}")
        print(f"Temperature: {item['temperature']} °C")
        print(f"Wind Speed: {item['wind_speed']} km/h")
        print(f"Weather: {item['description']}")
        print(f"Weather Code: {item['weather_code']}")


def get_weather():


        city_input = input(
            "Enter city or cities separated by comma: "
        )

        if "," not in city_input:

            city_obj = get_coordinates(city_input)

            weather = get_weather_data(
                city_obj.latitude,
                city_obj.longitude
            )

            save_weather(city_obj.name, weather)

            print(f"City: {city_obj.name}")
            print(f"Country: {city_obj.country}")
            print(f"Temperature: {weather.temperature} °C")
            print(f"Wind Speed: {weather.wind_speed} km/h")
            print(f"Weather: {get_weather_description(weather.weather_code)}")

        else:

            cities = city_input.split(",")

            def fetch_city(city_name):

                city_name = city_name.strip()

                city_obj = get_coordinates(city_name)

                weather = get_weather_data(
                    city_obj.latitude,
                    city_obj.longitude
                )

                return city_obj, weather

            with ThreadPoolExecutor(max_workers=5) as executor:

                futures = [
                    executor.submit(fetch_city, city)
                    for city in cities
                ]

                for future in as_completed(futures):
                    city_obj, weather = future.result()

                    save_weather(
                        city_obj.name,
                        weather
                    )

                    print("\n-------------------")
                    print(f"City: {city_obj.name}")
                    print(f"Country: {city_obj.country}")
                    print(f"Temperature: {weather.temperature} °C")
                    print(f"Wind Speed: {weather.wind_speed} km/h")
                    print(f"Weather: {get_weather_description(weather.weather_code)}")


def get_weather_description(code):
    weather_codes = {
        0: "Clear sky ☀️",
        1: "Mainly clear 🌤️",
        2: "Partly cloudy ⛅",
        3: "Overcast ☁️",
        45: "Fog 🌫️",
        48: "Depositing rime fog 🌫️",
        51: "Light drizzle 🌦️",
        53: "Moderate drizzle 🌦️",
        55: "Dense drizzle 🌧️",
        61: "Slight rain 🌧️",
        63: "Moderate rain 🌧️",
        65: "Heavy rain 🌧️",
        71: "Slight snow ❄️",
        73: "Moderate snow ❄️",
        75: "Heavy snow ❄️",
        80: "Rain showers 🌦️",
        95: "Thunderstorm ⛈️"
    }

    return weather_codes.get(code, "Unknown weather")

def save_city(city_obj):

    with open("cities.json", "r") as file:
        data = json.load(file)

    for item in data:
        if item["city"].lower() == city_obj.name.lower():
            print("City already exists!")
            return

    data.append({
        "city": city_obj.name,
        "country": city_obj.country,

        "latitude": city_obj.latitude,
        "longitude": city_obj.longitude

    })

    with open("cities.json", "w") as file:
        json.dump(data, file, indent=4)


def add_city():

    city = input("Enter city name: ")

    city_obj = get_coordinates(city)

    save_city(city_obj)

    print(f"✅ {city_obj.name} was saved!")



def remove_city():

    city = input("Enter city to remove: ")

    with open("cities.json", "r") as file:
        data = json.load(file)

    data = [
        item for item in data
        if item["city"].lower() != city.lower()
    ]

    with open("cities.json", "w") as file:
        json.dump(data, file, indent=4)

    print(f" {city} removed!")





def show_saved_cities():

    with open("cities.json", "r") as file:
        data = json.load(file)

    if not data:
        print("📍 No saved cities.")
        return

    for item in data:
        print("----------------")
        print(f"City: {item['city']}")
        print(f"Country: {item['country']}")

def create_map():

    with open("cities.json", "r") as file:
        data = json.load(file)

    if not data:
        print("📍 No saved cities.")
        return

    world_map = folium.Map(
        location=[20, 0],
        zoom_start=2
    )

    for item in data:
        folium.Marker(
            [item["latitude"], item["longitude"]],
            popup=f"{item['city']} ({item['country']})"
        ).add_to(world_map)

    world_map.save("cities_map.html")

    print("🌍 Map saved as cities_map.html")


while True:

    print("""
    ☁️ ☀️ 🌦️ 🌧️ ⛈️ ❄️ 🌈

        Welcome to My Weather Dashboard

    ☁️ ☀️ 🌦️ 🌧️ ⛈️ ❄️ 🌈

    1️:Weather
    2️:Show History
    3️:Add City
    4.Show Saved Cities
    5.Show Map
    6.Remove City
    7.Exit
    """)

    choice = input("👉 What do you want to do?: ").strip()

    if choice == "1":
        try:
            get_weather()
        except ValueError as error:
            print(error)

    elif choice == "2":
        show_history()


    elif choice == "3":
        try:
            add_city()
        except ValueError as error:
            print(error)

    elif choice == "4":
        show_saved_cities()

    elif choice == "5":
        create_map()
        webbrowser.open("cities_map.html")

    elif choice == "6":
        remove_city()

    elif choice == "7":
        print("Goodbye, thank you for using My Weather Dashboard!!")
        break

    else:
        print("Invalid option!")