import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    print("🔍 Testing ClickSafe API...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health endpoint: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Root endpoint: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return
    
    # Test prediction endpoint with a scam message
    test_messages = [
        "Click here to verify your account immediately! Your account will be suspended if you don't act now!",
        "Hello, this is a normal message about meeting tomorrow.",
        "ක්ලික් කරන්න ඔබගේ ගිණුම තහවුරු කිරීම සඳහා",
        "கிளிக் செய்யுங்கள் உங்கள் கணக்கை உறுதிப்படுத்த"
    ]
    
    for i, message in enumerate(test_messages, 1):
        try:
            response = requests.post(
                f"{base_url}/predict",
                json={"message": message},
                headers={"Content-Type": "application/json"}
            )
            print(f"\n✅ Test {i} - Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   Language: {result['language']}")
                print(f"   Classification: {result['classification']}")
                print(f"   Risk Score: {result['risk_score']}%")
                print(f"   Is Safe: {result['is_safe']}")
                print(f"   Explanation: {result['explanation'][:100]}...")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")

if __name__ == "__main__":
    test_api()