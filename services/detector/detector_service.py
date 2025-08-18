import os
import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from ultralytics import YOLO
import cv2
import numpy as np
import json

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
RAW_TOPIC = "cams.raw.frames"
DETECTIONS_TOPIC = "cams.detections"
TRACKS_TOPIC = "cams.tracks"

# Load YOLOv8 model (pretrained for vehicles)
model = YOLO('yolov8n.pt')  # You can use yolov8m.pt or yolov8l.pt for better accuracy

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
    try:
        async for msg in consumer:
            frame_bytes = msg.value
            frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
            results = model.track(frame, persist=True, tracker="bytetrack.yaml")
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
                            "class": model.names[cls],
                            "bbox": bbox,
                            "conf": conf
                        })
                # Tracks
                if hasattr(r, "boxes") and hasattr(r.boxes, "id"):
                    for box in r.boxes:
                        if box.id is not None and int(box.cls[0]) in [2, 3, 5, 7]:
                            tracks.append({
                                "track_id": int(box.id[0]),
                                "class": model.names[int(box.cls[0])],
                                "bbox": box.xyxy[0].tolist(),
                                "conf": float(box.conf[0])
                            })
            detection_msg = {
                "camera_id": msg.key.decode() if msg.key else None,
                "timestamp": msg.timestamp,
                "detections": detections
            }
            track_msg = {
                "camera_id": msg.key.decode() if msg.key else None,
                "timestamp": msg.timestamp,
                "tracks": tracks
            }
            await producer.send_and_wait(DETECTIONS_TOPIC, value=json.dumps(detection_msg).encode())
            await producer.send_and_wait(TRACKS_TOPIC, value=json.dumps(track_msg).encode())
            print(f"Published detections for {detection_msg['camera_id']} with {len(detections)} objects.")
            print(f"Published tracks for {track_msg['camera_id']} with {len(tracks)} objects.")
    finally:
        await consumer.stop()
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(process_frames())
