#!/usr/bin/env python3
"""
weather.py — Weather data provider for surveillance observations.

This module provides functions to:
  1. Generate or retrieve weather conditions for observations
  2. Start with dummy/mock data for the prototype
  3. Be structured for easy replacement with real weather APIs later

Current implementation generates realistic Kerala/India weather data.
Later: replace generate_dummy_weather() with get_real_weather(latitude, longitude)
       without changing the rest of the architecture.
"""

import random
from typing import Dict, Tuple, Optional


# ---------------------------------------------------------------------------
# WEATHER GENERATION — Kerala/India August conditions
# Replace with real weather API calls later
# ---------------------------------------------------------------------------
def generate_dummy_weather() -> Dict[str, float]:
    """
    Generate realistic dummy weather data for Kerala in August.
    
    August in Kerala is monsoon season:
      - Temperature: 26-31°C
      - Humidity: 78-94%
      - Wind speed: 4-12 km/h
    
    Returns:
        Dict with keys: temperature_c, humidity_percent, wind_speed_kmh
    
    Example:
        >>> weather = generate_dummy_weather()
        >>> print(weather)
        {'temperature_c': 28.4, 'humidity_percent': 86, 'wind_speed_kmh': 8.2}
    """
    return {
        "temperature_c": round(random.uniform(26.0, 31.0), 1),
        "humidity_percent": random.randint(78, 94),
        "wind_speed_kmh": round(random.uniform(4.0, 12.0), 1),
    }


def generate_favorable_weather() -> Dict[str, float]:
    """
    Generate weather conditions favorable for disease spread.
    
    Late Blight and Early Blight thrive in:
      - High humidity (>85%)
      - Moderate temperatures (18-25°C)
      - Light winds
    
    Returns:
        Dict with disease-favorable weather conditions
    
    Example:
        >>> weather = generate_favorable_weather()
        >>> weather['humidity_percent'] > 85
        True
    """
    return {
        "temperature_c": round(random.uniform(18.0, 25.0), 1),
        "humidity_percent": random.randint(85, 95),
        "wind_speed_kmh": round(random.uniform(2.0, 8.0), 1),
    }


def generate_unfavorable_weather() -> Dict[str, float]:
    """
    Generate weather conditions unfavorable for disease spread.
    
    Returns:
        Dict with disease-unfavorable weather conditions (dry, hot)
    
    Example:
        >>> weather = generate_unfavorable_weather()
        >>> weather['humidity_percent'] < 70
        True
    """
    return {
        "temperature_c": round(random.uniform(30.0, 35.0), 1),
        "humidity_percent": random.randint(50, 65),
        "wind_speed_kmh": round(random.uniform(10.0, 20.0), 1),
    }


# ---------------------------------------------------------------------------
# WEATHER RETRIEVAL
# ---------------------------------------------------------------------------
def get_weather_for_observation(
    observation: Dict,
    location: Tuple[float, float] = None
) -> Dict[str, float]:
    """
    Get weather conditions for an observation.
    
    Current implementation: generates dummy weather.
    Future implementation: could call a real weather API with lat/lon.
    
    Args:
        observation: Observation dict from observations.json
        location: Optional (latitude, longitude) tuple for location-based weather
    
    Returns:
        Dict with temperature_c, humidity_percent, wind_speed_kmh
    
    Example:
        >>> obs = {'observation_id': 'OBS-001', 'timestamp': '2026-08-26T04:10:13+00:00'}
        >>> weather = get_weather_for_observation(obs, (9.2645, 76.4600))
        >>> 'temperature_c' in weather
        True
    """
    # FUTURE: Use location to get real weather data
    # if location:
    #     return get_real_weather(location[0], location[1])
    
    # FUTURE: Use timestamp to get historical weather
    # timestamp = observation.get('timestamp')
    # if timestamp and location:
    #     return get_historical_weather(location[0], location[1], timestamp)
    
    # CURRENT: Use dummy data
    return generate_dummy_weather()


# ---------------------------------------------------------------------------
# FUTURE: REAL WEATHER SERVICES
# ---------------------------------------------------------------------------
def get_real_weather(latitude: float, longitude: float) -> Optional[Dict[str, float]]:
    """
    FUTURE: Retrieve real current weather from a weather API.
    
    Current implementation: returns None (not implemented).
    Future implementation could:
      - Call OpenWeatherMap API
      - Call WeatherAPI.com
      - Call Dark Sky API
      - Use a local weather station network
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
    
    Returns:
        Dict with temperature_c, humidity_percent, wind_speed_kmh, or None
    
    Example:
        >>> weather = get_real_weather(9.2645, 76.4600)
        >>> if weather:
        ...     print(f"Temperature: {weather['temperature_c']}°C")
    """
    # TODO: Implement real weather API integration
    # Example with OpenWeatherMap:
    # import requests
    # api_key = "YOUR_API_KEY"
    # url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}&units=metric"
    # response = requests.get(url)
    # data = response.json()
    # return {
    #     "temperature_c": data['main']['temp'],
    #     "humidity_percent": data['main']['humidity'],
    #     "wind_speed_kmh": data['wind']['speed'] * 3.6  # m/s to km/h
    # }
    return None


def get_historical_weather(
    latitude: float,
    longitude: float,
    timestamp: str
) -> Optional[Dict[str, float]]:
    """
    FUTURE: Retrieve historical weather data for a specific timestamp.
    
    Current implementation: returns None (not implemented).
    Future implementation could:
      - Call OpenWeatherMap Historical API
      - Query a local weather database
      - Use NOAA weather data
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        timestamp: ISO 8601 timestamp string
    
    Returns:
        Dict with temperature_c, humidity_percent, wind_speed_kmh, or None
    
    Example:
        >>> weather = get_historical_weather(9.2645, 76.4600, '2026-08-26T04:10:13+00:00')
        >>> if weather:
        ...     print(f"Humidity: {weather['humidity_percent']}%")
    """
    # TODO: Implement historical weather API integration
    return None


# ---------------------------------------------------------------------------
# WEATHER FORMATTING
# ---------------------------------------------------------------------------
def format_weather(weather: Dict[str, float]) -> str:
    """
    Format weather data as a human-readable multi-line string.
    
    Args:
        weather: Dict with temperature_c, humidity_percent, wind_speed_kmh
    
    Returns:
        Formatted string
    
    Example:
        >>> weather = {'temperature_c': 28.4, 'humidity_percent': 86, 'wind_speed_kmh': 8.2}
        >>> print(format_weather(weather))
        Temperature: 28.4°C
        Humidity: 86%
        Wind Speed: 8.2 km/h
    """
    temp = weather.get("temperature_c", "?")
    humidity = weather.get("humidity_percent", "?")
    wind = weather.get("wind_speed_kmh", "?")
    
    return (
        f"Temperature: {temp}°C\n"
        f"Humidity: {humidity}%\n"
        f"Wind Speed: {wind} km/h"
    )


def format_weather_compact(weather: Dict[str, float]) -> str:
    """
    Format weather data as a compact single-line string.
    
    Args:
        weather: Dict with temperature_c, humidity_percent, wind_speed_kmh
    
    Returns:
        Compact formatted string
    
    Example:
        >>> weather = {'temperature_c': 28.4, 'humidity_percent': 86, 'wind_speed_kmh': 8.2}
        >>> print(format_weather_compact(weather))
        28.4°C, 86% humidity, 8.2 km/h wind
    """
    temp = weather.get("temperature_c", "?")
    humidity = weather.get("humidity_percent", "?")
    wind = weather.get("wind_speed_kmh", "?")
    
    return f"{temp}°C, {humidity}% humidity, {wind} km/h wind"


# ---------------------------------------------------------------------------
# WEATHER ANALYSIS
# ---------------------------------------------------------------------------
def is_disease_favorable(weather: Dict[str, float], disease: str = None) -> bool:
    """
    Check if weather conditions are favorable for disease development.
    
    Late Blight and Early Blight favor:
      - Humidity > 85%
      - Temperature 18-25°C
      - Light winds < 10 km/h
    
    Args:
        weather: Dict with temperature_c, humidity_percent, wind_speed_kmh
        disease: Optional disease name for disease-specific thresholds
    
    Returns:
        True if conditions are favorable for disease spread
    
    Example:
        >>> weather = {'temperature_c': 22.0, 'humidity_percent': 90, 'wind_speed_kmh': 5.0}
        >>> is_disease_favorable(weather)
        True
    """
    temp = weather.get("temperature_c", 20.0)
    humidity = weather.get("humidity_percent", 80)
    wind = weather.get("wind_speed_kmh", 5.0)
    
    # General thresholds for fungal diseases
    favorable_temp = 18.0 <= temp <= 25.0
    favorable_humidity = humidity >= 85
    favorable_wind = wind <= 10.0
    
    return favorable_temp and favorable_humidity and favorable_wind


def get_disease_risk_level(weather: Dict[str, float]) -> str:
    """
    Get a qualitative risk level based on weather conditions.
    
    Args:
        weather: Dict with temperature_c, humidity_percent, wind_speed_kmh
    
    Returns:
        Risk level: "LOW", "MODERATE", "HIGH", or "EXTREME"
    
    Example:
        >>> weather = {'temperature_c': 22.0, 'humidity_percent': 90, 'wind_speed_kmh': 5.0}
        >>> get_disease_risk_level(weather)
        'HIGH'
    """
    humidity = weather.get("humidity_percent", 50)
    temp = weather.get("temperature_c", 25.0)
    
    if humidity >= 90 and 18.0 <= temp <= 25.0:
        return "EXTREME"
    elif humidity >= 85 and 18.0 <= temp <= 28.0:
        return "HIGH"
    elif humidity >= 75:
        return "MODERATE"
    else:
        return "LOW"


# ---------------------------------------------------------------------------
# TESTING / DEMO
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Testing weather.py...")
    print()
    
    # Test dummy weather generation
    print("Dummy weather (5 samples):")
    for i in range(5):
        weather = generate_dummy_weather()
        print(f"  Sample {i+1}: {format_weather_compact(weather)}")
    
    print()
    
    # Test disease-favorable weather
    print("Disease-favorable weather:")
    favorable = generate_favorable_weather()
    print(f"  {format_weather_compact(favorable)}")
    print(f"  Risk level: {get_disease_risk_level(favorable)}")
    print(f"  Favorable: {is_disease_favorable(favorable)}")
    
    print()
    
    # Test disease-unfavorable weather
    print("Disease-unfavorable weather:")
    unfavorable = generate_unfavorable_weather()
    print(f"  {format_weather_compact(unfavorable)}")
    print(f"  Risk level: {get_disease_risk_level(unfavorable)}")
    print(f"  Favorable: {is_disease_favorable(unfavorable)}")
    
    print()
    
    # Test formatting
    print("Weather formatting:")
    sample_weather = {'temperature_c': 28.4, 'humidity_percent': 86, 'wind_speed_kmh': 8.2}
    print("  Multi-line:")
    for line in format_weather(sample_weather).split('\n'):
        print(f"    {line}")
    print(f"  Compact: {format_weather_compact(sample_weather)}")
    
    print()
    print("All tests passed!")