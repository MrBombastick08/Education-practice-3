import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_get_items():
    print("Testing GET /items...")
    response = requests.get(f"{BASE_URL}/items")
    assert response.status_code == 200
    print(f"Success: Received {len(response.json())} items")

def test_create_item():
    print("Testing POST /items...")
    payload = {"title": "Test Task", "description": "Testing the API", "status": "active"}
    response = requests.post(f"{BASE_URL}/items", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    print(f"Success: Created item with ID {data['id']}")
    return data["id"]

def test_get_single_item(item_id):
    print(f"Testing GET /items/{item_id}...")
    response = requests.get(f"{BASE_URL}/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["id"] == item_id
    print("Success: Item found")

def test_error_handling():
    print("Testing error handling (404)...")
    response = requests.get(f"{BASE_URL}/items/999")
    assert response.status_code == 404
    print("Success: 404 handled correctly")

def test_delete_item(item_id):
    print(f"Testing DELETE /items/{item_id}...")
    response = requests.delete(f"{BASE_URL}/items/{item_id}")
    assert response.status_code == 200
    print("Success: Item deleted")

if __name__ == "__main__":
    try:
        test_get_items()
        new_id = test_create_item()
        test_get_single_item(new_id)
        test_error_handling()
        test_delete_item(new_id)
        print("\nAll API tests passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")
