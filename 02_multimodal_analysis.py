"""
Module 2: Multimodal CV & Environmental Parameters Pipeline
-----------------------------------------------------------
Demonstrates programmatic querying of point environmental variables
and overhead satellite view land-cover segmentation.
"""

import os
import time
import json
import base64
import requests

API_KEY = os.getenv("FORTYGUARD_API_KEY", "PASTE_YOUR_API_KEY_HERE")
BASE_URL = "https://api.fortyguard.com/v1"

HEADERS = {
    "api-key": API_KEY,
    "Content-Type": "application/json"
}

def test_environmental_parameters():
    """
    Tests POST /v1/env_params for point-level thermal stress,
    air quality, and solar irradiance metrics.
    """
    endpoint = f"{BASE_URL}/env_params"
    
    # Request weather, air quality, and solar parameters for New York City
    payload = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "temperature": 32.5,  # °C supplied reference temperature
        "date_time": {
            "start_date": "2024-07-15",
            "start_time": "14:00",
            "filter_type": 1  # Single Hour
        },
        "analysis": [
            "heat_index_celsius",
            "apparent_temperature_celsius",
            "wet_bulb_temperature_celsius",
            "air_quality:idx",
            "solar_irradiance"
        ]
    }

    print("🌿 [Evaluation Note: POST /v1/env_params]")
    print("   Querying atmospheric and air quality parameters...")

    t0 = time.perf_counter()
    response = requests.post(endpoint, headers=HEADERS, json=payload)
    latency_ms = (time.perf_counter() - t0) * 1000

    print(f"   HTTP Status: {response.status_code} (Latency: {latency_ms:.1f} ms)")

    if response.status_code != 200:
        print(f"❌ Env Params Error: {response.text}")
        return

    json_resp = response.json()
    # Note: env_params is synchronous or returns data directly depending on tier/load
    print("✅ Environmental Parameters Response Received Successfully!")
    print(json.dumps(json_resp, indent=2)[:500] + "\n... [truncated for display]\n")


def test_satellite_segmentation():
    """
    Tests POST /v1/satellite for land-cover semantic segmentation.
    Note: Requires API Premium and consumes 14,400 credits.
    """
    endpoint = f"{BASE_URL}/satellite"
    
    payload = {
        "sat": {
            "latitude": 40.7128,
            "longitude": -74.0060
        },
        "date_time": {
            "start_date": "2024-07-15",
            "start_time": "14:00",
            "filter_type": 1
        },
        "granularity": 80
    }

    print("🛰️ [Evaluation Note: POST /v1/satellite]")
    print("   Submitting satellite imagery segmentation request (14,400 credit cost)...")

    response = requests.post(endpoint, headers=HEADERS, json=payload)
    print(f"   HTTP Status: {response.status_code}")

    if response.status_code == 403:
        print("🔒 [Expected on Trial/Basic Keys]: 403 Forbidden - Insufficient plan tier (API Premium required for satellite endpoint).")
        return
    elif response.status_code not in (200, 201, 202):
        print(f"❌ Satellite Error: {response.text}")
        return

    data = response.json().get("data", {})
    activity_id = data.get("activity_id")
    print(f"✅ Satellite Task Accepted! Activity ID: {activity_id}")
    
    # If synchronous data is returned immediately vs activity_id
    if "Segmentation" in data:
        print("   Segmentation results returned inline!")
        segments = data["Segmentation"].get("segments", {})
        print("   Class Coverage Percentages:", json.dumps(segments, indent=2))


if __name__ == "__main__":
    print("=== FortyGuard Module 2 Test: Multimodal Analysis ===")
    test_environmental_parameters()
    print("-" * 50)
    test_satellite_segmentation()