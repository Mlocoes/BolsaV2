import requests
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

def verify_delete():
    print("Verifying DELETE Endpoint...")
    base_url = "http://localhost:8000/api/assets"
    
    # 1. Create a dummy asset
    print("Creating dummy asset...")
    try:
        response = requests.post(base_url, json={
            "symbol": "DELETE_ME",
            "name": "Asset to Delete",
            "asset_type": "stock",
            "currency": "USD"
        })
        
        if response.status_code == 201:
            asset_id = response.json()["id"]
            print(f"✅ Asset created: {asset_id}")
        elif response.status_code == 400 and "Ya existe" in response.text:
            # Search for it to get ID
            print("Asset already exists, searching...")
            search_resp = requests.get(f"{base_url}/search?q=DELETE_ME")
            asset_id = search_resp.json()[0]["id"]
            print(f"Found existing asset: {asset_id}")
        else:
            print(f"❌ Failed to create asset: {response.status_code} - {response.text}")
            return

        # 2. Delete it
        print(f"Deleting asset {asset_id}...")
        del_response = requests.delete(f"{base_url}/{asset_id}")
        
        if del_response.status_code == 204:
            print("✅ DELETE request successful (204 No Content)")
        elif del_response.status_code == 405:
            print("❌ DELETE request failed: 405 Method Not Allowed")
        else:
            print(f"❌ DELETE request failed: {del_response.status_code} - {del_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_delete()
