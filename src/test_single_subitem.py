#!/usr/bin/env python3
"""
Test Monday.com API - Add Single Subitem

This script adds one test subitem to verify the API is working.
"""

import requests
import json
from datetime import datetime, timedelta


def test_monday_api():
    """Test adding a single subitem to Monday.com."""
    
    # Your API token
    API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjU2OTEzMjQwMiwiYWFpIjoxMSwidWlkIjoyNTU3NDU5OSwiaWFkIjoiMjAyNS0xMC0wMVQyMzo0NTo0OC40NjRaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MzM3OTc2MywicmduIjoidXNlMSJ9.XCcD2sOVi5HP1o14pyD0Q8MFhJqBwlqFgKfC8UXpRMM"
    
    # Monday.com API endpoint
    url = "https://api.monday.com/v2"
    
    headers = {
        "Authorization": API_TOKEN,
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing Monday.com API")
    print("=" * 40)
    
    # Step 1: Get the SS26 Prod Dev board
    print("📋 Step 1: Finding SS26 Prod Dev board...")
    
    query = """
    query {
        boards {
            id
            name
            groups {
                id
                title
            }
        }
    }
    """
    
    payload = {"query": query}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            print(f"❌ GraphQL errors: {data['errors']}")
            return
        
        boards = data.get("data", {}).get("boards", [])
        
        # Find SS26 Prod Dev board (exact match, not subitems)
        target_board = None
        for board in boards:
            if board["name"] == "SS26 Prod Dev":
                target_board = board
                break
        
        if not target_board:
            print("❌ SS26 Prod Dev board not found")
            print("Available boards:")
            for board in boards:
                print(f"  - {board['name']} (ID: {board['id']})")
            return
        
        print(f"✅ Found board: {target_board['name']} (ID: {target_board['id']})")
        
        # Step 2: Find the "SS New Colors" group
        print("\n📦 Step 2: Finding SS New Colors group...")
        
        target_group = None
        for group in target_board["groups"]:
            if "SS New Colors" in group["title"]:
                target_group = group
                print(f"✅ Found group: {group['title']} (ID: {group['id']})")
                break
        
        if not target_group:
            print("❌ SS New Colors group not found")
            print("Available groups:")
            for group in target_board["groups"]:
                print(f"  - {group['title']} (ID: {group['id']})")
            return
        
        # Step 3: Get items from the group
        print("\n🔍 Step 3: Finding Item 1...")
        
        items_query = f"""
        query {{
            boards(ids: ["{target_board['id']}"]) {{
                items_page {{
                    items {{
                        id
                        name
                        group {{
                            id
                            title
                        }}
                    }}
                }}
            }}
        }}
        """
        
        items_payload = {"query": items_query}
        items_response = requests.post(url, headers=headers, json=items_payload, timeout=30)
        items_response.raise_for_status()
        
        items_data = items_response.json()
        
        if "errors" in items_data:
            print(f"❌ Items query errors: {items_data['errors']}")
            return
        
        items = items_data.get("data", {}).get("boards", [{}])[0].get("items_page", {}).get("items", [])
        
        print(f"Looking for items in group ID: {target_group['id']}")
        print("Items and their groups:")
        for item in items:
            group_info = item.get("group", {})
            print(f"  - {item['name']} -> Group: {group_info.get('title', 'Unknown')} (ID: {group_info.get('id', 'Unknown')})")
        
        # Use the first available item (Kilo Hoodie Battleship)
        target_item = items[0] if items else None
        
        if not target_item:
            print("❌ No items found in the board")
            return
        
        print(f"✅ Using item: {target_item['name']} (ID: {target_item['id']})")
        
        # Step 3: Create the test subitem
        print("\n🔧 Step 3: Creating test subitem...")
        
        subitem_query = """
        mutation($parentItemId: ID!, $subitemName: String!) {
            create_subitem(parent_item_id: $parentItemId, item_name: $subitemName) {
                id
                name
            }
        }
        """
        
        subitem_payload = {
            "query": subitem_query,
            "variables": {
                "parentItemId": target_item["id"],
                "subitemName": "test sub api"
            }
        }
        
        subitem_response = requests.post(url, headers=headers, json=subitem_payload, timeout=30)
        subitem_response.raise_for_status()
        
        subitem_data = subitem_response.json()
        
        if "errors" in subitem_data:
            print(f"❌ Subitem creation errors: {subitem_data['errors']}")
            return
        
        subitem = subitem_data.get("data", {}).get("create_subitem")
        
        if subitem:
            print(f"🎉 SUCCESS! Created subitem: {subitem['name']} (ID: {subitem['id']})")
            print(f"🔗 View your board: https://your-account.monday.com/boards/{target_board['id']}")
        else:
            print("❌ Failed to create subitem")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out. Please check your internet connection.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    test_monday_api()
