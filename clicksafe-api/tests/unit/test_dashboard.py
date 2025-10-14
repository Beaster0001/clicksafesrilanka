#!/usr/bin/env python3

import requests
import json

def test_dashboard_api():
    print("=== TESTING DASHBOARD API ===")
    
    # First, let's try without authentication
    try:
        response = requests.get("http://localhost:8000/dashboard/")
        print(f"Dashboard without auth: Status {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error calling dashboard without auth: {e}")
    
    # Test with dummy token (will fail but show error)
    try:
        headers = {"Authorization": "Bearer dummy-token"}
        response = requests.get("http://localhost:8000/dashboard/", headers=headers)
        print(f"Dashboard with dummy token: Status {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error calling dashboard with dummy token: {e}")

if __name__ == "__main__":
    test_dashboard_api()