
import os
import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from ultralytics import YOLO
import cv2
import numpy as np
import json
from collections import defaultdict

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
RAW_TOPIC = "cams.raw.frames"
DETECTIONS_TOPIC = "cams.detections"
TRACKS_TOPIC = "cams.tracks"


# Use a separate YOLO tracker per camera
camera_trackers = defaultdict(lambda: YOLO('yolov8n.pt'))  # You can use yolov8m.pt or yolov8l.pt for better accuracy

async def process_frames():
    consumer = AIOKafkaConsumer(
        RAW_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_deserializer=lambda v: v,
        key_deserializer=lambda k: k,
        auto_offset_reset='latest',
        group_id='detector-group'
    )
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)
    await consumer.start()
    await producer.start()
    # --- Speed calculation state ---
    # For each camera, track_id: store last position and timestamp
    prev_track_state = defaultdict(dict)  # camera_id -> track_id -> {"pos": (x, y), "timestamp": t}
    # Pixel to meter conversion (adjust as needed for your camera)
    PIXELS_PER_METER = 10.0  # Example: 10 pixels = 1 meter
    try:
        async for msg in consumer:
            camera_id = msg.key.decode() if msg.key else None
            frame_bytes = msg.value
            frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
            # Use a separate tracker per camera
            tracker_model = camera_trackers[camera_id]
            results = tracker_model.track(frame, persist=True, tracker="bytetrack.yaml")
            detections = []
            tracks = []
            for r in results:
                # Detections
                for box in r.boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    bbox = box.xyxy[0].tolist()
                    if cls in [2, 3, 5, 7]:
                        detections.append({
                            "class": tracker_model.names[cls],
                            "bbox": bbox,
                            "conf": conf
                        })
                # Tracks (debug: print all box attributes)
                for box in r.boxes:
                    print(f"DEBUG: box attrs: id={getattr(box, 'id', None)}, cls={getattr(box, 'cls', None)}, conf={getattr(box, 'conf', None)}, bbox={getattr(box, 'xyxy', None)}")
                    if hasattr(box, "id") and box.id is not None:
                        cls = int(box.cls[0])
                        if cls in [2, 3, 5, 7]:
                            track_id = int(box.id[0])
                            bbox = box.xyxy[0].tolist()
                            # Use bbox center for position
                            x = (bbox[0] + bbox[2]) / 2
                            y = (bbox[1] + bbox[3]) / 2
                            pos = (x, y)
                            timestamp = msg.timestamp / 1000.0  # Convert ms to seconds
                            speed_mps = None
                            prev = prev_track_state[camera_id].get(track_id)
                            if prev:
                                dx = pos[0] - prev["pos"][0]
                                dy = pos[1] - prev["pos"][1]
                                dt = timestamp - prev["timestamp"]
                                if dt > 0:
                                    dist_pixels = np.sqrt(dx**2 + dy**2)
                                    dist_meters = dist_pixels / PIXELS_PER_METER
                                    speed_mps = dist_meters / dt
                            # Update state
                            prev_track_state[camera_id][track_id] = {"pos": pos, "timestamp": timestamp}
                            tracks.append({
                                "track_id": track_id,
                                "class": tracker_model.names[cls],
                                "bbox": bbox,
                                "conf": float(box.conf[0]),
                                "timestamp": msg.timestamp,
                                "speed": speed_mps if speed_mps is not None else 0.0
                            })
            detection_msg = {
                "camera_id": camera_id,
                "timestamp": msg.timestamp,
                "detections": detections
            }
            track_msg = {
                "camera_id": camera_id,
                "timestamp": msg.timestamp,
                "tracks": tracks
            }
            await producer.send_and_wait(DETECTIONS_TOPIC, value=json.dumps(detection_msg).encode())
            await producer.send_and_wait(TRACKS_TOPIC, value=json.dumps(track_msg).encode())
            print(f"Consumed frame from {detection_msg['camera_id']} at {detection_msg['timestamp']}")
            print(f"Published detections to {DETECTIONS_TOPIC}: {len(detections)} objects.")
            print(f"Published tracks to {TRACKS_TOPIC}: {len(tracks)} objects.")
    finally:
        await consumer.stop()
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(process_frames())
