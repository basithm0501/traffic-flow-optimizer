import requests

url = "http://127.0.0.1:8000/infer"
image_path = "frames_511ny/Skyline-13982_1755530198.jpg"  # Using a sample image from frames_511ny

with open(image_path, "rb") as f:
    files = {"file": (image_path, f, "image/jpeg")}
    response = requests.post(url, files=files)
    print(response.status_code)
    print(response.json())
