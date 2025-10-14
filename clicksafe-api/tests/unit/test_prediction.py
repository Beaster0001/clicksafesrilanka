import requests
import json

# Test the prediction endpoint
url = "http://localhost:8000/predict"
data = {
    "message": "Hello, this is a test message",
    "language": "english"
}

try:
    response = requests.post(url, json=data)
    print("Status Code:", response.status_code)
    print("Response:", response.json())
except Exception as e:
    print("Error:", e)