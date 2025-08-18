import requests
import os
import time
import asyncio
from dotenv import load_dotenv
import json
from math import radians, cos, sin, sqrt, atan2
from aiokafka import AIOKafkaProducer


# Load environment variables from .env file in traffic-opt folder
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
API_KEY = os.getenv("API_KEY")
API_URL = "https://511ny.org/api/GetCameras?key={key}&format=json"

# Output directory for downloaded images
OUTPUT_DIR = "frames_511ny"
os.makedirs(OUTPUT_DIR, exist_ok=True)

LOCATIONS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'locations.geojson')
def load_locations():
    with open(LOCATIONS_PATH) as f:
        geo = json.load(f)
    locations = []
    for feat in geo['features']:
        name = feat['properties']['name']
        lon, lat = feat['geometry']['coordinates']
        locations.append({'name': name, 'lat': lat, 'lon': lon})
    return locations

# Haversine distance in meters
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def fetch_cameras(api_key):
    url = API_URL.format(key=api_key)
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching cameras: {response.status_code}")
        return []
    return response.json()

def match_cameras(cameras, locations, max_dist=100):
    # max_dist in meters
    matched = []
    for cam in cameras:
        cam_lat = cam.get('Latitude')
        cam_lon = cam.get('Longitude')
        cam_name = cam.get('Name', '').lower()
        for loc in locations:
            dist = haversine(cam_lat, cam_lon, loc['lat'], loc['lon'])
            if dist < max_dist or loc['name'].lower() in cam_name:
                matched.append(cam)
                break
    return matched

    # Function no longer needed; replaced by fetch_and_publish


async def fetch_and_publish(cam, producer, interval=2):
    while True:
        try:
            resp = requests.get(cam["Url"], timeout=5)
            if resp.status_code == 200:
                jpeg_bytes = resp.content
                ts_ms = str(int(time.time() * 1000)).encode()
                key = cam["ID"].encode()
                headers = [
                    ("camera_id", key),
                    ("ts_ms", ts_ms),
                    ("codec", b"jpg"),
                ]
                await producer.send_and_wait("cams.raw.frames", value=jpeg_bytes, key=key, headers=headers)
                print(f"Published frame from {cam['Name']}")
            else:
                print(f"Failed {cam['ID']} status {resp.status_code}")
        except Exception as e:
            print(f"Error fetching {cam['ID']}: {e}")
        await asyncio.sleep(interval)

async def main():
    locations = load_locations()
    cameras = fetch_cameras(API_KEY)
    print(f"Found {len(cameras)} cameras from API.")
    matched = match_cameras(cameras, locations)
    print(f"Matched {len(matched)} cameras to intersections.")

    producer = AIOKafkaProducer(bootstrap_servers="localhost:9092")
    await producer.start()
    try:
        await asyncio.gather(*(fetch_and_publish(cam, producer) for cam in matched))
    finally:
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(main())

def fetch_cameras(api_key):
    url = API_URL.format(key=api_key)
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching cameras: {response.status_code}")
        return []
    # The API returns a list, not a dict
    return response.json()

