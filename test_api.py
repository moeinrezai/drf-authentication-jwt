import requests
import time

BASE_URL = "http://localhost:8000/api/accounts/v1"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36"
}

def test_register():
    print("🔹 Testing Registration...")
    resp = requests.post(f"{BASE_URL}/register/", json={
        "email": "test@example.com",
        "name": "Test User",
        "password": "TestPass123",
        "password2": "TestPass123"
    }, headers=HEADERS)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 201:
        data = resp.json()
        print(f"   ✅ Access Token: {data['access'][:30]}...")
        return data["access"], data["refresh"]
    else:
        print(f"   ❌ Error: {resp.text}")
        return None, None

def test_login():
    print("🔹 Testing Login...")
    resp = requests.post(f"{BASE_URL}/login/", json={
        "email": "test@example.com",
        "password": "TestPass123"
    }, headers=HEADERS)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✅ Access Token: {data['access'][:30]}...")
        return data["access"], data["refresh"]
    else:
        print(f"   ❌ Error: {resp.text}")
        return None, None

def test_profile(access_token):
    print("🔹 Testing Profile...")
    auth_headers = {**HEADERS, "Authorization": f"Bearer {access_token}"}
    resp = requests.get(f"{BASE_URL}/profile/", headers=auth_headers)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"   ✅ Data: {resp.json()}")
    else:
        print(f"   ❌ Error: {resp.text}")

def test_fingerprint(access_token):
    print("🔹 Testing Fingerprint (different User-Agent)...")
    bad_headers = {
        **HEADERS,
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "Mozilla/5.0 (iPhone) AppleWebKit/537.36"
    }
    resp = requests.get(f"{BASE_URL}/profile/", headers=bad_headers)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 401:
        print(f"   ✅ Fingerprint protection works!")
    else:
        print(f"   ❌ Error: {resp.text}")

def test_rate_limit():
    print("🔹 Testing Rate Limiting...")
    for i in range(6):
        resp = requests.post(f"{BASE_URL}/login/", json={
            "email": "test@example.com",
            "password": "TestPass123"
        }, headers=HEADERS)
        print(f"   Request {i+1}: {resp.status_code}")
        time.sleep(0.1)
    print("   ✅ Rate limiting test completed")

def test_refresh(refresh_token):
    print("🔹 Testing Token Refresh...")
    resp = requests.post(f"{BASE_URL}/refresh/", json={
        "refresh": refresh_token
    }, headers=HEADERS)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✅ New Access Token: {data['access'][:30]}...")
        return data["access"], data["refresh"]
    else:
        print(f"   ❌ Error: {resp.text}")
        return None, None

def test_logout(access_token, refresh_token):
    print("🔹 Testing Logout...")
    auth_headers = {**HEADERS, "Authorization": f"Bearer {access_token}"}
    resp = requests.post(f"{BASE_URL}/logout/", json={
        "refresh": refresh_token
    }, headers=auth_headers)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"   ✅ Logout successful")
    else:
        print(f"   ❌ Error: {resp.text}")

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Starting API Tests")
    print("=" * 50)
    
    # Test Registration
    access, refresh = test_register()
    if not access:
        # Try login if user exists
        access, refresh = test_login()
    
    if access:
        test_profile(access)
        test_fingerprint(access)
        test_rate_limit()
        access, refresh = test_refresh(refresh)
        if access:
            test_logout(access, refresh)
    
    print("=" * 50)
    print("✅ All Tests Completed")
    print("=" * 50)