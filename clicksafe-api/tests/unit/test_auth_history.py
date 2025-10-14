"""
Test Scan History with Authentication
"""
from auth import create_access_token
from datetime import timedelta
import requests
import json
from database import SessionLocal
from models import User

# Get user and create token
db = SessionLocal()
user = db.query(User).filter(User.email == 'chamika@gmail.com').first()
token = create_access_token(data={'sub': str(user.id)}, expires_delta=timedelta(hours=24))
db.close()

headers = {'Authorization': f'Bearer {token}'}

print("🔍 Testing authenticated QR scanning (should save to history)...")

# Scan a QR code with authentication
try:
    with open('test_google_qr.png', 'rb') as f:
        files = {'file': ('test_google_qr.png', f, 'image/png')}
        response = requests.post('http://localhost:8000/api/qr/scan/image', files=files, headers=headers)
    
    if response.status_code == 200:
        print('✅ QR scan with authentication successful')
    else:
        print(f'❌ QR scan failed: {response.text}')
except Exception as e:
    print(f'❌ QR scan error: {e}')

print("\n🔗 Testing authenticated URL analysis (should save to history)...")

# Analyze a URL with authentication
try:
    data = {"url": "https://suspicious-example.com", "save_to_history": True}
    response = requests.post('http://localhost:8000/api/qr/scan/url', json=data, headers=headers)
    
    if response.status_code == 200:
        print('✅ URL analysis with authentication successful')
    else:
        print(f'❌ URL analysis failed: {response.text}')
except Exception as e:
    print(f'❌ URL analysis error: {e}')

print("\n📚 Testing scan history retrieval...")

# Get scan history
try:
    response = requests.get('http://localhost:8000/api/qr/scan/history', headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print('✅ Scan history retrieved successfully!')
        print(f'Total scans: {result.get("total_count", 0)}')
        
        scans = result.get("scans", [])
        if scans:
            print(f'Recent scans:')
            for scan in scans[:3]:  # Show first 3
                print(f'  - {scan.get("scan_type")}: {scan.get("content")[:50]}... (Risk: {scan.get("risk_score")})')
        else:
            print('No scan history found')
    else:
        print(f'❌ Scan history failed: {response.text}')
except Exception as e:
    print(f'❌ Scan history error: {e}')

print("\n🎉 Authenticated tests completed!")