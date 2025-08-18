from fastapi import FastAPI, UploadFile, File
from ultralytics import YOLO
import cv2
import numpy as np
import json

app = FastAPI()
model = YOLO('yolov8n.pt')  # Use a different model if needed

@app.post("/infer")
async def infer_image(file: UploadFile = File(...)):
    contents = await file.read()
    frame = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
    results = model.track(frame, persist=True, tracker="bytetrack.yaml")
    detections = []
    tracks = []
    for r in results:
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
            if box.id is not None and cls in [2, 3, 5, 7]:
                tracks.append({
                    "track_id": int(box.id[0]),
                    "class": model.names[cls],
                    "bbox": bbox,
                    "conf": conf
                })
    return {
        "detections": detections,
        "tracks": tracks
    }

# To run: uvicorn detector_api:app --reload
