"""
Quick test script for Journal API
Run this after starting the server to verify the API works correctly
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "YOUR_JWT_TOKEN_HERE"  # Replace with actual token from login

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}


def test_quick_text_entry():
    """Test quick text journal entry"""
    print("\n=== Testing Quick Text Entry ===")

    url = f"{BASE_URL}/journals/quick"
    data = {
        "entry_type": "text",
        "content": "Today was an amazing day! I learned so much about gratitude."
    }

    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.json()


def test_full_journal_entry():
    """Test full journal entry creation"""
    print("\n=== Testing Full Journal Entry ===")

    url = f"{BASE_URL}/journals/create"
    data = {
        "title": "My Reflection on Today",
        "content": "Today I learned about gratitude and mindfulness...",
        "entry_type": "text",
        "privacy": "private",
        "is_favorite": False
    }

    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.json()


def test_full_entry_with_tags():
    """Test journal entry with tag auto-creation"""
    print("\n=== Testing Entry with Tags ===")

    url = f"{BASE_URL}/journals/create"
    data = {
        "title": "Gratitude Practice",
        "content": "Three things I'm grateful for today...",
        "entry_type": "text",
        "tag_names": ["gratitude", "mindfulness", "daily-practice"]
    }

    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.json()


def test_list_entries():
    """Test listing journal entries"""
    print("\n=== Testing List Entries ===")

    url = f"{BASE_URL}/journals/list?page=1&limit=5"

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.json()


def test_create_tag():
    """Test creating a tag"""
    print("\n=== Testing Create Tag ===")

    url = f"{BASE_URL}/journals/tags/create"
    data = {
        "name": "wellness",
        "color": "#10B981"
    }

    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.json()


def test_list_tags():
    """Test listing tags"""
    print("\n=== Testing List Tags ===")

    url = f"{BASE_URL}/journals/tags"

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.json()


def run_all_tests():
    """Run all tests"""
    print("=" * 50)
    print("Journal API Test Suite")
    print("=" * 50)

    if TOKEN == "YOUR_JWT_TOKEN_HERE":
        print("\n⚠️  ERROR: Please set your JWT token in the TOKEN variable")
        print("Get your token by:")
        print("1. POST /api/v1/authentication/login")
        print("2. Copy the 'access' token from response")
        print("3. Replace TOKEN variable above")
        return

    try:
        # Test 1: Quick text entry
        test_quick_text_entry()

        # Test 2: Full entry
        test_full_journal_entry()

        # Test 3: Entry with tags
        test_full_entry_with_tags()

        # Test 4: Create tag
        test_create_tag()

        # Test 5: List tags
        test_list_tags()

        # Test 6: List entries
        test_list_entries()

        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        print("=" * 50)

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server")
        print("Make sure the server is running:")
        print("  python manage.py runserver")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


if __name__ == "__main__":
    run_all_tests()
