import cv2
import time

# Replace with your RTSP/MJPEG camera feed URL
CAMERA_URL = "<YOUR_CAMERA_FEED_URL>"

# Output directory for saved frames (optional)
OUTPUT_DIR = "frames"

# Create output directory if needed
import os
os.makedirs(OUTPUT_DIR, exist_ok=True)

def capture_frames(camera_url, output_dir, interval=1):
    cap = cv2.VideoCapture(camera_url)
    if not cap.isOpened():
        print(f"Error: Cannot open camera feed: {camera_url}")
        return
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        # Save frame as JPEG
        frame_path = os.path.join(output_dir, f"frame_{frame_count:05d}.jpg")
        cv2.imwrite(frame_path, frame)
        print(f"Saved {frame_path}")
        frame_count += 1
        time.sleep(interval)
    cap.release()

if __name__ == "__main__":
    capture_frames(CAMERA_URL, OUTPUT_DIR)
