import os
from typing import Optional

import requests
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import tool


class WeatherInput(BaseModel):
    city: str = Field(..., description="The city name to get weather for")
    state: str = Field(
        ..., description="The two letter state abbreviation to get weather for"
    )
    country: Optional[str] = Field(
        "usa", description="The two letter country abbreviation to get weather for"
    )


@tool("weather-data", args_schema=WeatherInput, return_direct=True)
def weather_data(city: str, state: str, country: str = "usa") -> dict:
    """Get the current temperature for a city."""
    geocode_api_key = os.environ.get("GEOCODE_API_KEY")
    if not geocode_api_key:
        raise ValueError("Missing GEOCODE_API_KEY secret.")

    geocode_url = f"https://geocode.xyz/{city.lower()},{state.lower()},{country.lower()}?json=1&auth={geocode_api_key}"
    geocode_response = requests.get(geocode_url)
    if not geocode_response.ok:
        print("No geocode data found.")
        raise ValueError("Failed to get geocode data.")
    geocode_data = geocode_response.json()
    latt = geocode_data["latt"]
    longt = geocode_data["longt"]

    weather_gov_url = f"https://api.weather.gov/points/{latt},{longt}"
    weather_gov_response = requests.get(weather_gov_url)
    if not weather_gov_response.ok:
        print("No weather data found.")
        raise ValueError("Failed to get weather data.")
    weather_gov_data = weather_gov_response.json()
    properties = weather_gov_data["properties"]

    forecast_url = properties["forecast"]
    forecast_response = requests.get(forecast_url)
    if not forecast_response.ok:
        print("No forecast data found.")
        raise ValueError("Failed to get forecast data.")
    forecast_data = forecast_response.json()
    periods = forecast_data["properties"]["periods"]
    today_forecast = periods[0]

    return {
        "city": city,
        "state": state,
        "country": country,
        "temperature": today_forecast["temperature"],
    }


class QWeatherInput(BaseModel):
    city: str = Field(..., description="城市名称")
    adm: Optional[str] = Field(
        None,
        description="城市的上级行政区划，如请求参数为location=朝阳&adm=北京时，返回的结果只包括北京市的朝阳区，而不包括辽宁省的朝阳市",
    )


@tool("qweather-data", args_schema=QWeatherInput, return_direct=True)
def qweather_data(city: str, adm: Optional[str] = None) -> dict:
    """调用和风天气 API, 获取天气信息"""
    api_key = os.environ.get("QWEATHER_API_KEY")
    if not api_key:
        raise ValueError("Missing QWEATHER_API_KEY secret.")

    # 获取城市代码
    location_url = (
        f"https://geoapi.qweather.com/v2/city/lookup?location={city}"
        f"{'&adm=' + adm if adm else ''}&key={api_key}"
    )
    location_response = requests.get(location_url)
    if not location_response.ok:
        print("No location data found.")
        raise ValueError("Failed to get location data.")
    location_data = location_response.json()
    location_id = location_data["location"][0]["id"]

    # 查询天气
    weather_url = f"https://devapi.qweather.com/v7/weather/now?location={location_id}&key={api_key}"
    weather_response = requests.get(weather_url)
    if not weather_response.ok:
        print("No weather data found.")
        raise ValueError("Failed to get weather data.")
    weather_data = weather_response.json()
    now = weather_data["now"]

    return {
        "city": city,
        "temperature": now["temp"],
        "weather": now["text"],
    }
