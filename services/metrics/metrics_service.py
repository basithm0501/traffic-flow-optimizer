import os
import json
import numpy as np
from collections import defaultdict, deque
from datetime import datetime
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import asyncio
import cv2

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TRACKS_TOPIC = "cams.tracks"
METRICS_TOPIC = "metrics.minute"

# Example lane config (should be loaded from config/db)
lane_config = {
    # ================================
    # CAM: MONROE @ WINTON  (Skyline-5557)
    # ================================
    # View: wide SE corner; intersection in lower half; main corridor left↔right along top-third
    "monroe_winton_wb_thru_1": {
        "camera_id": "cam_5557",
        "polygon": [(0,110),(140,110),(140,140),(0,140)]
    },
    "monroe_winton_wb_thru_2": {
        "camera_id": "cam_5557",
        "polygon": [(0,140),(150,140),(150,165),(0,165)]
    },
    "monroe_winton_eb_thru_1": {
        "camera_id": "cam_5557",
        "polygon": [(210,105),(351,105),(351,140),(210,140)]
    },
    "monroe_winton_eb_thru_2": {
        "camera_id": "cam_5557",
        "polygon": [(200,140),(351,140),(351,170),(200,170)]
    },
    "monroe_winton_sb_approach": {  # from top center down toward the intersection
        "camera_id": "cam_5557",
        "polygon": [(150,40),(225,60),(205,120),(140,110)]
    },
    "monroe_winton_nb_right": {     # near-bottom right corner slip/egress (small)
        "camera_id": "cam_5557",
        "polygon": [(270,185),(351,175),(351,239),(230,239)]
    },

    # ================================
    # CAM: WINTON & ELMWOOD  (Skyline-13982)
    # ================================
    # View: corridor runs vertical; camera on SW corner looking NE; stop bar across near-bottom
    "winton_elmwood_nb_right": {
        "camera_id": "cam_13982",
        "polygon": [(185,95),(230,95),(230,200),(185,200)]
    },
    "winton_elmwood_nb_middle": {
        "camera_id": "cam_13982",
        "polygon": [(230,90),(275,90),(275,200),(230,200)]
    },
    "winton_elmwood_nb_left": {
        "camera_id": "cam_13982",
        "polygon": [(275,85),(330,85),(330,200),(275,200)]
    },
    "winton_elmwood_sb_left": {   # opposing approach lanes (far side of intersection)
        "camera_id": "cam_13982",
        "polygon": [(25,65),(75,65),(75,140),(25,140)]
    },
    "winton_elmwood_sb_middle": {
        "camera_id": "cam_13982",
        "polygon": [(75,60),(125,60),(125,135),(75,135)]
    },
    "winton_elmwood_sb_right": {
        "camera_id": "cam_13982",
        "polygon": [(125,55),(175,55),(175,130),(125,130)]
    },
    "winton_elmwood_wb_leftturn_bay": {  # short bay on near-left
        "camera_id": "cam_13982",
        "polygon": [(0,150),(80,150),(80,200),(0,200)]
    },

    # ================================
    # CAM: NY31 @ NY65 / MONROE AVE @ CLOVER ST  (Skyline-16133)
    # ================================
    # View: major E↔W arterial; camera on near-right corner looking NW; crosswalk diagonals visible
    "monroe_clover_eb_right": {
        "camera_id": "cam_16133",
        "polygon": [(140,150),(220,150),(220,190),(140,190)]
    },
    "monroe_clover_eb_middle": {
        "camera_id": "cam_16133",
        "polygon": [(220,145),(285,145),(285,190),(220,190)]
    },
    "monroe_clover_eb_left": {
        "camera_id": "cam_16133",
        "polygon": [(285,140),(351,140),(351,190),(285,190)]
    },
    "monroe_clover_wb_right": {
        "camera_id": "cam_16133",
        "polygon": [(0,165),(70,165),(70,205),(0,205)]
    },
    "monroe_clover_wb_middle": {
        "camera_id": "cam_16133",
        "polygon": [(70,160),(140,160),(140,205),(70,205)]
    },
    "monroe_clover_wb_left": {
        "camera_id": "cam_16133",
        "polygon": [(140,155),(200,155),(200,200),(140,200)]
    },
    "monroe_clover_nb_rightturn_island": {  # small channelized right-turn pocket near bottom-right
        "camera_id": "cam_16133",
        "polygon": [(300,200),(351,195),(351,239),(290,239)]
    }
}


# Helper: assign track to lane by bbox center
def assign_lane(bbox, lane_config):
    cx = (bbox[0] + bbox[2]) / 2
    cy = (bbox[1] + bbox[3]) / 2
    for lane_id, lane in lane_config.items():
        # Simple point-in-polygon (replace with shapely for real use)
        poly = np.array(lane["polygon"])
        if cv2.pointPolygonTest(poly, (cx, cy), False) >= 0:
            return lane_id
    return None

# State for per-minute aggregation
class MetricsAggregator:
    def __init__(self):
        self.tracks = defaultdict(lambda: deque())  # lane_id -> deque of (track info)
        self.last_minute = None

    def add_track(self, track, lane_id, timestamp):
        self.tracks[lane_id].append((track, timestamp))

    def compute_metrics(self, minute):
        metrics = {}
        for lane_id, track_deque in self.tracks.items():
            # Filter tracks for this minute
            tracks = [t for t, ts in track_deque if ts // 60 == minute]
            if not tracks:
                continue
            # Volume by class
            volume = defaultdict(int)
            for t in tracks:
                volume[t["class"]] += 1
            # Queue length: max number of vehicles present
            queue_length = len(tracks)
            # Average speed: mean of speeds (meters/sec)
            avg_speed = np.mean([t.get("speed", 0) for t in tracks]) if tracks else 0
            # Occupancy: fraction of time lane is occupied
            occupancy = min(1.0, queue_length / 10)  # Placeholder
            # --- Headway calculation ---
            # Sort tracks by timestamp
            timestamps = sorted([t.get("timestamp", 0) for t in tracks])
            headways = []
            for i in range(1, len(timestamps)):
                dt = (timestamps[i] - timestamps[i-1]) / 1000.0  # ms to seconds
                if dt > 0:
                    headways.append(dt)
            avg_headway = np.mean(headways) if headways else 0
            # Turn proportions: count by turn type
            turn_props = defaultdict(int)
            for t in tracks:
                turn_props[t.get("turn", "straight")] += 1
            metrics[lane_id] = {
                "volume": dict(volume),
                "queue_length": queue_length,
                "avg_speed": avg_speed,
                "occupancy": occupancy,
                "avg_headway": avg_headway,
                "turn_proportions": dict(turn_props)
            }
        return metrics

async def process_tracks():
    consumer = AIOKafkaConsumer(
        TRACKS_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_deserializer=lambda v: json.loads(v),
        auto_offset_reset='latest',
        group_id='metrics-group'
    )
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)
    await consumer.start()
    await producer.start()
    aggregator = MetricsAggregator()
    try:
        async for msg in consumer:
            track_msg = msg.value
            timestamp = track_msg.get("timestamp", int(datetime.utcnow().timestamp()))
            print(f"DEBUG: Full track_msg: {json.dumps(track_msg)[:500]}")
            tracks = track_msg.get('tracks', [])
            print(f"DEBUG: tracks field type: {type(tracks)}, length: {len(tracks)}")
            if tracks:
                print(f"DEBUG: First track: {json.dumps(tracks[0])}")
            print(f"Consumed track message at {timestamp} with {len(tracks)} tracks.")
            for track in tracks:
                lane_id = assign_lane(track["bbox"], lane_config)
                if lane_id:
                    aggregator.add_track(track, lane_id, timestamp)
            minute = timestamp // 60
            if aggregator.last_minute is None:
                aggregator.last_minute = minute
            if minute != aggregator.last_minute:
                metrics = aggregator.compute_metrics(aggregator.last_minute)
                metrics_msg = {
                    "minute": aggregator.last_minute,
                    "metrics": metrics
                }
                await producer.send_and_wait(METRICS_TOPIC, value=json.dumps(metrics_msg).encode())
                print(f"Published metrics for minute {aggregator.last_minute} to {METRICS_TOPIC}")
                aggregator.last_minute = minute
    finally:
        await consumer.stop()
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(process_tracks())
