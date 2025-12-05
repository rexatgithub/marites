#!/usr/bin/env python3

import requests
import json
import sys
from urllib.parse import urljoin


def test_health(base_url):
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get(urljoin(base_url, '/health'))
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_index(base_url):
    print("\n🏠 Testing index endpoint...")
    try:
        response = requests.get(base_url)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:3000"

    print(f"🧪 Testing Marites at {base_url}")
    print("=" * 60)

    results = {
        'health': test_health(base_url),
        'index': test_index(base_url),
    }

    print("\n" + "=" * 60)
    print("📊 Test Results:")
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test}: {status}")

    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()

