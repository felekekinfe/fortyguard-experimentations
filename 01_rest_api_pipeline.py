"""
Module 1: FortyGuard REST API & Asynchronous Polling Pipeline
-------------------------------------------------------------
This script demonstrates how to interact with FortyGuard's async engine,
handle eventual consistency delays (404s right after submission), and parse
the resulting spatial statistics.
"""

import os
import time
import json
import requests

# 1. Configuration & Authentication
# We use an environment variable with a fallback to your trial key string.
API_KEY = os.getenv("FORTYGUARD_API_KEY", "PASTE_YOUR_API_KEY_HERE")
BASE_URL = "https://api.fortyguard.com/v1"

HEADERS = {
    "api-key": API_KEY,
    "Content-Type": "application/json"
}

def submit_heatmap_job():
    """Submits an asynchronous heatmap task to the FortyGuard Engine."""
    endpoint = f"{BASE_URL}/heatmap"
    
    # Define a bounding polygon over Lower Manhattan, NY
    payload = {
        "polygon_aoi": {
            "type": "Polygon",
            "coordinates": [[
                [-74.0170, 40.7051],
                [-74.0031, 40.7051],
                [-74.0031, 40.7180],
                [-74.0170, 40.7180],
                [-74.0170, 40.7051]
            ]]
        },
        "date_time": {
            "start_date": "2024-07-15",
            "start_time": "14:00",
            "filter_type": 1  # Single Hour filter
        },
        "granularity": 100
    }

    print("🚀 [Evaluation Note: POST /v1/heatmap]")
    print("   Sending AOI polygon and date configuration...")
    
    t0 = time.perf_counter()
    response = requests.post(endpoint, headers=HEADERS, json=payload)
    latency_ms = (time.perf_counter() - t0) * 1000

    print(f"   HTTP Status: {response.status_code} (TTFB Latency: {latency_ms:.1f} ms)")

    # Evaluation check: Always validate status codes before parsing JSON
    if response.status_code not in (200, 201, 202):
        print(f"❌ Error Response: {response.text}")
        return None

    data = response.json().get("data", {})
    activity_id = data.get("activity_id")
    print(f"✅ Job accepted successfully! Activity ID: {activity_id}\n")
    return activity_id


def poll_task_status(activity_id, max_attempts=60, sleep_sec=5):
    """
    Polls GET /v1/status/{activity_id} with bounded retries.
    Includes handling for temporary 404 eventual consistency windows.
    """
    status_url = f"{BASE_URL}/status/{activity_id}"
    print(f"🔄 [Evaluation Note: GET /v1/status/{activity_id}]")
    print(f"   Beginning bounded polling loop (max {max_attempts * sleep_sec}s)...")

    start_time = time.perf_counter()

    for attempt in range(1, max_attempts + 1):
        response = requests.get(status_url, headers={"api-key": API_KEY})
        
        # Engineering Note: Docs note a temporary 404 can occur immediately after submission
        if response.status_code == 404:
            print(f"   [Attempt {attempt:02d}] 404 Not Found (eventual consistency lag) -> retrying in {sleep_sec}s")
            time.sleep(sleep_sec)
            continue

        if response.status_code != 200:
            print(f"❌ Polling HTTP Error {response.status_code}: {response.text}")
            return None

        status_json = response.json().get("data", {})
        status = str(status_json.get("status", "")).lower()
        elapsed = time.perf_counter() - start_time

        print(f"   [Attempt {attempt:02d} | {elapsed:.1f}s] Current Status: {status_json.get('status')}")

        if status in ("completed", "succeeded"):
            print(f"\n🎉 Task completed successfully in {elapsed:.2f} seconds!")
            return status_json.get("result", {})
        elif status in ("failed", "error"):
            print(f"\n❌ Task failed on server: {json.dumps(status_json, indent=2)}")
            return None
        else:
            time.sleep(sleep_sec)

    print("\n⏰ Polling timed out before completion.")
    return None


if __name__ == "__main__":
    print("=== FortyGuard Module 1 Test: REST Pipeline ===")
    
    # 1. Submit job
    job_id = submit_heatmap_job()
    
    if job_id:
        # 2. Poll for results
        result_payload = poll_task_status(job_id)
        
        if result_payload:
            stats = result_payload.get("stats_data", {})
            print("\n📊 Extracted Temperature Statistics (stats_data):")
            print(json.dumps(stats, indent=2))
            
            features = result_payload.get("map_data", {}).get("features", [])
            print(f"\n🗺️ Total GeoJSON Map Tiles Received: {len(features)}")