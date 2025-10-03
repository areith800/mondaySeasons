#!/usr/bin/env python3
"""
Add Subitems to Monday.com Boards

This script reads your CSV data and adds subitems with due dates to Monday.com boards.
"""

import csv
import json
from datetime import datetime, timedelta
from monday_api_client import MondayAPIClient


def parse_launch_date(launch_date_str):
    """Parse launch date from Excel serial number or date string."""
    if not launch_date_str or launch_date_str.strip() == '':
        return None
    
    # Handle Excel serial date numbers (like 45930)
    try:
        if launch_date_str.isdigit():
            excel_date = int(launch_date_str)
            # Convert Excel serial date to Python date
            base_date = datetime(1899, 12, 30)  # Excel's epoch
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


def calculate_due_date(launch_date, lead_time_weeks):
    """Calculate due date by subtracting lead time from launch date."""
    if launch_date is None:
        return None
    
    due_date = launch_date - timedelta(weeks=lead_time_weeks)
    return due_date.strftime('%Y-%m-%d')


def main():
    """Main function to add subitems to Monday.com."""
    
    # Your API token
    API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjU2OTEzMjQwMiwiYWFpIjoxMSwidWlkIjoyNTU3NDU5OSwiaWFkIjoiMjAyNS0xMC0wMVQyMzo0NTo0OC40NjRaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MzM3OTc2MywicmduIjoidXNlMSJ9.XCcD2sOVi5HP1o14pyD0Q8MFhJqBwlqFgKfC8UXpRMM"
    
    # Initialize Monday.com client
    client = MondayAPIClient(API_TOKEN)
    
    print("🚀 Monday.com Subitem Manager")
    print("=" * 50)
    
    # Get available boards
    print("📋 Available boards:")
    boards = client.get_boards()
    for i, board in enumerate(boards[:10], 1):  # Show first 10 boards
        print(f"  {i}. {board['name']} (ID: {board['id']})")
    
    # Let user choose a board
    try:
        choice = input("\nEnter board number (1-10) or board name: ").strip()
        
        # Try to parse as number first
        try:
            board_index = int(choice) - 1
            if 0 <= board_index < len(boards):
                selected_board = boards[board_index]
            else:
                print("Invalid board number")
                return
        except ValueError:
            # Try to find by name
            selected_board = None
            for board in boards:
                if choice.lower() in board['name'].lower():
                    selected_board = board
                    break
            
            if not selected_board:
                print(f"Board '{choice}' not found")
                return
        
        print(f"\n✅ Selected board: {selected_board['name']}")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        return
    
    # Read CSV data
    csv_file = "SS26_ProdDev.csv"
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            csv_data = list(reader)
        print(f"📊 Loaded {len(csv_data)} rows from {csv_file}")
    except FileNotFoundError:
        print(f"❌ CSV file '{csv_file}' not found")
        return
    
    # Setup due date column
    board_id = selected_board['id']
    try:
        due_date_column_id = client.get_or_create_due_date_column(board_id, "Due Date")
        print(f"📅 Due date column ready (ID: {due_date_column_id})")
    except Exception as e:
        print(f"⚠️  Warning: Could not setup due date column: {e}")
        due_date_column_id = None
    
    # Define subitems with lead times (in weeks)
    subitems_config = [
        {"name": "Fabric Approved", "lead_time_weeks": 40},
        {"name": "Design Approved", "lead_time_weeks": 26},
        {"name": "Fit Approved", "lead_time_weeks": 18},
        {"name": "Color Approved", "lead_time_weeks": 16},
        {"name": "Production Approved", "lead_time_weeks": 12}
    ]
    
    # Process each main item
    items_created = 0
    subitems_created = 0
    
    for row in csv_data:
        # Skip empty rows or subitems
        if not row.get('Name') or row.get('Name').startswith('Subitems'):
            continue
        
        item_name = row.get('Name', '').strip()
        if not item_name:
            continue
        
        print(f"\n📦 Processing: {item_name}")
        
        # Parse launch date
        launch_date_str = row.get('Launch Date', '')
        launch_date = parse_launch_date(launch_date_str)
        
        if not launch_date:
            print(f"  ⚠️  No valid launch date, skipping subitems")
            continue
        
        print(f"  📅 Launch date: {launch_date.strftime('%Y-%m-%d')}")
        
        # Create main item
        try:
            # Prepare column values
            column_values = {
                'text': row.get('Style-Color', ''),
                'text1': row.get('Color Name', ''),
                'text2': row.get('Person', ''),
                'text3': row.get('Status', ''),
                'date': launch_date.strftime('%Y-%m-%d')
            }
            
            # Remove empty values
            column_values = {k: v for k, v in column_values.items() if v}
            
            main_item = client.create_item(board_id, item_name, column_values)
            print(f"  ✅ Created main item: {main_item['name']} (ID: {main_item['id']})")
            items_created += 1
            
            # Create subitems
            for subitem_config in subitems_config:
                subitem_name = subitem_config['name']
                lead_time_weeks = subitem_config['lead_time_weeks']
                
                # Calculate due date
                due_date = calculate_due_date(launch_date, lead_time_weeks)
                
                # Prepare subitem column values
                subitem_column_values = {
                    'status': 'Not Started'
                }
                
                # Add due date if column is available
                if due_date_column_id and due_date:
                    subitem_column_values[due_date_column_id] = due_date
                
                # Remove empty values
                subitem_column_values = {k: v for k, v in subitem_column_values.items() if v}
                
                subitem = client.create_subitem(
                    main_item['id'],
                    subitem_name,
                    subitem_column_values
                )
                
                print(f"    ✅ {subitem_name} (Due: {due_date})")
                subitems_created += 1
            
        except Exception as e:
            print(f"  ❌ Error creating item: {e}")
            continue
    
    print(f"\n🎉 Summary:")
    print(f"  📦 Main items created: {items_created}")
    print(f"  📋 Subitems created: {subitems_created}")
    print(f"  🔗 View your board: https://your-account.monday.com/boards/{board_id}")


if __name__ == "__main__":
    main()
