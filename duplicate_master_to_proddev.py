#!/usr/bin/env python3
"""
Duplicate SS26 Master Board to SS26 Prod Dev Board

This script duplicates all items from SS26 Master Board to SS26 Prod Dev Board
with matching groups and adds subitems based on monday_config.json.
"""

import requests
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class MondayBoardDuplicator:
    """Handles duplication of items between Monday.com boards."""
    
    def __init__(self, api_token: str):
        """Initialize with API token."""
        self.api_token = api_token
        self.base_url = "https://api.monday.com/v2"
        self.headers = {
            "Authorization": api_token,
            "Content-Type": "application/json"
        }
    
    def _make_request(self, query: str, variables: Dict = None) -> Dict:
        """Make a GraphQL request to Monday.com API."""
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "errors" in data:
                raise Exception(f"GraphQL errors: {data['errors']}")
            
            return data.get("data", {})
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    def get_board_by_name(self, board_name: str) -> Optional[Dict]:
        """Find a board by name."""
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
        
        data = self._make_request(query)
        boards = data.get("boards", [])
        
        for board in boards:
            if board["name"] == board_name:
                return board
        return None
    
    def get_board_items(self, board_id: str) -> List[Dict]:
        """Get all items from a board with their groups."""
        query = f"""
        query {{
            boards(ids: ["{board_id}"]) {{
                items_page(limit: 500) {{
                    items {{
                        id
                        name
                        group {{
                            id
                            title
                        }}
                        column_values {{
                            id
                            text
                            value
                        }}
                    }}
                }}
            }}
        }}
        """
        
        data = self._make_request(query)
        items = data.get("boards", [{}])[0].get("items_page", {}).get("items", [])
        print(f"Retrieved {len(items)} items from board")
        return items
    
    def get_board_columns(self, board_id: str) -> List[Dict]:
        """Get column information for a board."""
        query = f"""
        query {{
            boards(ids: ["{board_id}"]) {{
                columns {{
                    id
                    title
                    type
                }}
            }}
        }}
        """
        
        data = self._make_request(query)
        return data.get("boards", [{}])[0].get("columns", [])
    
    def create_group(self, board_id: str, group_name: str) -> Dict:
        """Create a new group in a board."""
        query = """
        mutation($boardId: ID!, $groupName: String!) {
            create_group(board_id: $boardId, group_name: $groupName) {
                id
                title
            }
        }
        """
        
        variables = {
            "boardId": board_id,
            "groupName": group_name
        }
        
        data = self._make_request(query, variables)
        return data["create_group"]
    
    def get_or_create_group(self, board_id: str, group_name: str) -> str:
        """Get existing group or create new one."""
        # First, get all groups in the board
        query = f"""
        query {{
            boards(ids: ["{board_id}"]) {{
                groups {{
                    id
                    title
                }}
            }}
        }}
        """
        
        data = self._make_request(query)
        groups = data.get("boards", [{}])[0].get("groups", [])
        
        # Look for existing group
        for group in groups:
            if group["title"] == group_name:
                return group["id"]
        
        # Create new group
        group_data = self.create_group(board_id, group_name)
        return group_data["id"]
    
    def create_item(self, board_id: str, group_id: str, item_name: str, column_values: Dict = None) -> Dict:
        """Create a new item in a specific group."""
        query = """
        mutation($boardId: ID!, $groupId: String!, $itemName: String!, $columnValues: JSON!) {
            create_item(board_id: $boardId, group_id: $groupId, item_name: $itemName, column_values: $columnValues) {
                id
                name
            }
        }
        """
        
        variables = {
            "boardId": board_id,
            "groupId": group_id,
            "itemName": item_name,
            "columnValues": json.dumps(column_values or {})
        }
        
        data = self._make_request(query, variables)
        return data["create_item"]
    
    def create_subitem(self, parent_item_id: str, subitem_name: str, column_values: Dict = None) -> Dict:
        """Create a subitem under a parent item."""
        query = """
        mutation($parentItemId: ID!, $subitemName: String!, $columnValues: JSON!) {
            create_subitem(parent_item_id: $parentItemId, item_name: $subitemName, column_values: $columnValues) {
                id
                name
            }
        }
        """
        
        variables = {
            "parentItemId": parent_item_id,
            "subitemName": subitem_name,
            "columnValues": json.dumps(column_values or {})
        }
        
        data = self._make_request(query, variables)
        return data["create_subitem"]
    
    def parse_launch_date(self, launch_date_str: str) -> Optional[datetime]:
        """Parse launch date from Excel serial number or date string."""
        if not launch_date_str or launch_date_str.strip() == '':
            return None
        
        # Handle Excel serial date numbers
        try:
            if launch_date_str.isdigit():
                excel_date = int(launch_date_str)
                base_date = datetime(1899, 12, 30)
                return base_date + timedelta(days=excel_date)
        except ValueError:
            pass
        
        # Handle standard date formats
        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']
        for fmt in date_formats:
            try:
                return datetime.strptime(launch_date_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    def calculate_due_date(self, launch_date: datetime, lead_time_weeks: int) -> str:
        """Calculate due date by subtracting lead time from launch date."""
        if launch_date is None:
            return None
        
        due_date = launch_date - timedelta(weeks=lead_time_weeks)
        return due_date.strftime('%Y-%m-%d')
    
    def duplicate_master_to_proddev(self):
        """Main function to duplicate items from Master to Prod Dev board."""
        
        print("🚀 SS26 Master to Prod Dev Duplicator")
        print("=" * 50)
        
        # Load configuration
        try:
            with open('monday_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            print("❌ monday_config.json not found")
            return
        
        # Get boards
        print("📋 Finding boards...")
        master_board = self.get_board_by_name("SS26 Master")
        proddev_board = self.get_board_by_name("SS26 Prod Dev")
        
        if not master_board:
            print("❌ SS26 Master board not found")
            return
        
        if not proddev_board:
            print("❌ SS26 Prod Dev board not found")
            return
        
        print(f"✅ Found Master board: {master_board['name']} (ID: {master_board['id']})")
        print(f"✅ Found Prod Dev board: {proddev_board['name']} (ID: {proddev_board['id']})")
        
        # Get items from Master board
        print("\n📦 Getting items from Master board...")
        master_items = self.get_board_items(master_board['id'])
        print(f"Found {len(master_items)} items in Master board")
        
        # Get column mappings
        print("\n📋 Getting column mappings...")
        master_columns = self.get_board_columns(master_board['id'])
        proddev_columns = self.get_board_columns(proddev_board['id'])
        
        # Find Platform column in both boards
        master_platform_col = None
        proddev_platform_col = None
        
        for col in master_columns:
            if 'platform' in col['title'].lower():
                master_platform_col = col
                break
        
        for col in proddev_columns:
            if 'platform' in col['title'].lower():
                proddev_platform_col = col
                break
        
        if master_platform_col and proddev_platform_col:
            print(f"✅ Platform column mapping: {master_platform_col['title']} -> {proddev_platform_col['title']}")
        else:
            print("⚠️  Platform column not found in one or both boards")
        
        # Define target groups
        target_groups = ["SS26 New Colors", "SS26 New Styles", "End of Life Products"]
        
        # Create groups in Prod Dev board
        print("\n🏗️ Setting up groups in Prod Dev board...")
        group_mapping = {}
        for group_name in target_groups:
            group_id = self.get_or_create_group(proddev_board['id'], group_name)
            group_mapping[group_name] = group_id
            print(f"✅ Group '{group_name}' ready (ID: {group_id})")
        
        # Get subitems configuration
        subitems_config = config['departments']['Product Development']['sub_items']
        print(f"\n📋 Subitems configuration loaded: {len(subitems_config)} subitems")
        
        # Process each master item
        items_created = 0
        subitems_created = 0
        
        print(f"\n🔄 Processing {len(master_items)} items...")
        
        for i, item in enumerate(master_items, 1):
            try:
                # Show progress every 10 items
                if i % 10 == 0 or i == 1:
                    print(f"\n[{i}/{len(master_items)}] Processing: {item['name']}")
                else:
                    print(f"[{i}/{len(master_items)}] {item['name']}")
                
                # Determine target group based on item's current group in Master board
                current_group = item.get('group', {}).get('title', '')
                
                # Map Master board groups to Prod Dev board groups
                if "new colors" in current_group.lower():
                    target_group_name = "SS26 New Colors"
                elif "new styles" in current_group.lower():
                    target_group_name = "SS26 New Styles"
                elif "end of life" in current_group.lower():
                    target_group_name = "End of Life Products"
                else:
                    target_group_name = "SS26 New Colors"  # Default group
                
                target_group_id = group_mapping[target_group_name]
                
                # Extract column values from master item
                column_values = {}
                platform_value = None
                
                for col in item.get('column_values', []):
                    col_text = col.get('text', '')
                    col_id = col.get('id', '')
                    
                    # Look for Platform column specifically
                    if master_platform_col and col_id == master_platform_col['id']:
                        platform_value = col_text
                    
                    # Copy other relevant fields (but not Platform yet)
                    if col_text and col_id and col_id != master_platform_col['id']:
                        column_values[col_id] = col_text
                
                # Add Platform field if found and target column exists
                if platform_value and proddev_platform_col:
                    column_values[proddev_platform_col['id']] = platform_value
                    print(f"  📱 Platform: {platform_value}")
                
                # Create item in Prod Dev board
                new_item = self.create_item(
                    proddev_board['id'],
                    target_group_id,
                    item['name'],
                    column_values
                )
                
                print(f"  ✅ Created item: {new_item['name']} (ID: {new_item['id']})")
                items_created += 1
                
                # Add subitems
                # Try to find launch date from column values
                launch_date = None
                for col in item.get('column_values', []):
                    if 'launch' in col.get('id', '').lower() or 'date' in col.get('id', '').lower():
                        launch_date = self.parse_launch_date(col.get('text', ''))
                        if launch_date:
                            break
                
                if launch_date:
                    if i % 10 == 0 or i == 1:
                        print(f"  📅 Launch date: {launch_date.strftime('%Y-%m-%d')}")
                    
                    for subitem_config in subitems_config:
                        subitem_name = subitem_config['task_name']
                        lead_time_weeks = subitem_config['lead_time_weeks']
                        
                        # Calculate due date
                        due_date = self.calculate_due_date(launch_date, lead_time_weeks)
                        
                        # Create subitem
                        subitem_column_values = {
                            'status': 'Working on it'  # Use valid status from the board
                        }
                        
                        if due_date:
                            subitem_column_values['date'] = due_date
                        
                        subitem = self.create_subitem(
                            new_item['id'],
                            subitem_name,
                            subitem_column_values
                        )
                        
                        if i % 10 == 0 or i == 1:
                            print(f"    ✅ {subitem_name} (Due: {due_date})")
                        subitems_created += 1
                else:
                    if i % 10 == 0 or i == 1:
                        print(f"  ⚠️  No launch date found, creating subitems without due dates")
                    for subitem_config in subitems_config:
                        subitem_name = subitem_config['task_name']
                        
                        subitem = self.create_subitem(
                            new_item['id'],
                            subitem_name,
                            {'status': 'Working on it'}
                        )
                        
                        if i % 10 == 0 or i == 1:
                            print(f"    ✅ {subitem_name}")
                        subitems_created += 1
                
                # Add small delay to avoid rate limiting (reduced for speed)
                import time
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  ❌ Error processing item: {e}")
                continue
        
        print(f"\n🎉 Duplication Complete!")
        print(f"  📦 Items created: {items_created}")
        print(f"  📋 Subitems created: {subitems_created}")
        print(f"  🔗 View your board: https://your-account.monday.com/boards/{proddev_board['id']}")


def main():
    """Main function."""
    API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjU2OTEzMjQwMiwiYWFpIjoxMSwidWlkIjoyNTU3NDU5OSwiaWFkIjoiMjAyNS0xMC0wMVQyMzo0NTo0OC40NjRaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MzM3OTc2MywicmduIjoidXNlMSJ9.XCcD2sOVi5HP1o14pyD0Q8MFhJqBwlqFgKfC8UXpRMM"
    
    duplicator = MondayBoardDuplicator(API_TOKEN)
    duplicator.duplicate_master_to_proddev()


if __name__ == "__main__":
    main()
