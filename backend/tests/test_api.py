import requests
import sys

BASE_URL = "http://localhost:8000"

def test_backend():
    print("--- TESTING BACKEND API ---")
    
    # 1. Test Status
    try:
        res = requests.get(f"{BASE_URL}/api/status")
        print(f"[PASS] Status: {res.json()}")
    except Exception as e:
        print(f"[FAIL] Status: {e}")
        return

    # 2. Test Projects
    try:
        res = requests.get(f"{BASE_URL}/api/projects")
        print(f"[PASS] Projects found: {len(res.json())}")
    except Exception as e:
        print(f"[FAIL] Projects: {e}")

    # 3. Test Deep Dive Analysis (Search)
    print("Testing AI Deep Dive (this may take 10s)...")
    try:
        res = requests.get(f"{BASE_URL}/api/analyze/0700.HK")
        if res.status_code == 200:
            print(f"[PASS] Analysis for 0700.HK: {res.json()['recommendation']} (Score: {res.json()['confidence']})")
        else:
            print(f"[FAIL] Analysis failed with status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[FAIL] Analysis: {e}")

if __name__ == "__main__":
    test_backend()
