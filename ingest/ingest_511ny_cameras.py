


import requests
import os
import time
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import json
from math import radians, cos, sin, sqrt, atan2
from kafka import KafkaProducer


# Load environment variables from .env file in traffic-opt folder
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
API_KEY = os.getenv("API_KEY")
API_URL = "https://511ny.org/api/GetCameras?key={key}&format=json"

# Output directory for downloaded images
OUTPUT_DIR = "frames_511ny"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load intersection locations from geojson
LOCATIONS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'locations.geojson')
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

def download_and_publish_image(image_url, camera_id, output_dir, producer=None, topic=None):
    try:
        resp = requests.get(image_url, timeout=10)
        if resp.status_code == 200:
            img_bytes = resp.content
            img = Image.open(BytesIO(img_bytes))
            img_path = os.path.join(output_dir, f"{camera_id}_{int(time.time())}.jpg")
            img.save(img_path)
            print(f"Saved {img_path}")
            # Publish to Kafka
            if producer and topic:
                ts = int(time.time() * 1000)
                headers = [
                    ("camera_id", camera_id.encode()),
                    ("timestamp", str(ts).encode())
                ]
                producer.send(topic, key=camera_id.encode(), value=img_bytes, headers=headers)
                print(f"Published frame for {camera_id} to Kafka topic {topic}")
        else:
            print(f"Failed to download image for {camera_id}: {resp.status_code}")
    except Exception as e:
        print(f"Error downloading image for {camera_id}: {e}")


def main():
    locations = load_locations()
    cameras = fetch_cameras(API_KEY)
    print(f"Found {len(cameras)} cameras from API.")
    matched = match_cameras(cameras, locations)
    print(f"Matched {len(matched)} cameras to intersections.")

    # Kafka setup
    producer = KafkaProducer(
        bootstrap_servers=["localhost:9092"],
        value_serializer=lambda v: v,
        key_serializer=lambda k: k
    )
    topic = "cams.raw.frames"

    for cam in matched:
        camera_id = cam.get("ID")
        image_url = cam.get("Url")
        if camera_id and image_url:
            download_and_publish_image(image_url, camera_id, OUTPUT_DIR, producer, topic)
        time.sleep(6)  # Respect API rate limits

    producer.flush()

if __name__ == "__main__":
    main()

def fetch_cameras(api_key):
    url = API_URL.format(key=api_key)
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching cameras: {response.status_code}")
        return []
    return response.json().get("Cameras", [])

def download_camera_image(image_url, camera_id, output_dir):
    try:
        resp = requests.get(image_url, timeout=10)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            img_path = os.path.join(output_dir, f"{camera_id}_{int(time.time())}.jpg")
            img.save(img_path)
            print(f"Saved {img_path}")
        else:
            print(f"Failed to download image for {camera_id}: {resp.status_code}")
    except Exception as e:
        print(f"Error downloading image for {camera_id}: {e}")

def main():
    cameras = fetch_cameras(API_KEY)
    print(f"Found {len(cameras)} cameras.")
    for cam in cameras:
        camera_id = cam.get("Id")
        image_url = cam.get("ImageUrl")
        if camera_id and image_url:
            download_camera_image(image_url, camera_id, OUTPUT_DIR)
        time.sleep(1)  # Respect API rate limits

if __name__ == "__main__":
    main()
