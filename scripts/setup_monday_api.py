#!/usr/bin/env python3
"""
Monday.com API Setup Script

This script helps you set up and test your Monday.com API integration.
"""

import json
import os
from monday_api_client import MondayAPIClient


def setup_api_token():
    """Help user set up their API token."""
    print("Monday.com API Setup")
    print("=" * 50)
    print()
    print("To use the Monday.com API, you need an API token.")
    print("You can get your API token from: https://auth.monday.com/users/sign_in")
    print()
    
    api_token = input("Enter your Monday.com API token: ").strip()
    
    if not api_token:
        print("No API token provided. Exiting.")
        return None
    
    # Save token to environment variable
    os.environ['MONDAY_API_TOKEN'] = api_token
    
    # Also save to a config file for convenience
    config = {
        "api_token": api_token,
        "base_url": "https://api.monday.com/v2"
    }
    
    with open('monday_api_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("API token saved to monday_api_config.json")
    return api_token


def test_api_connection(api_token):
    """Test the API connection."""
    print("\nTesting API connection...")
    
    try:
        client = MondayAPIClient(api_token)
        boards = client.get_boards()
        
        print(f"✅ Successfully connected to Monday.com API")
        print(f"Found {len(boards)} boards:")
        
        for board in boards[:5]:  # Show first 5 boards
            print(f"  - {board['name']} (ID: {board['id']})")
        
        if len(boards) > 5:
            print(f"  ... and {len(boards) - 5} more boards")
        
        return True
        
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False


def create_sample_board(client):
    """Create a sample board for testing."""
    print("\nCreating sample board for testing...")
    
    try:
        board_name = "Product Development Test Board"
        
        # Check if board already exists
        existing_board = client.get_board_by_name(board_name)
        if existing_board:
            print(f"Board '{board_name}' already exists (ID: {existing_board['id']})")
            return existing_board
        
        # Create new board
        board = client.create_board(board_name)
        print(f"✅ Created board: {board['name']} (ID: {board['id']})")
        
        # Add due date column
        due_date_column = client.add_due_date_column(board['id'], "Due Date")
        print(f"✅ Added due date column: {due_date_column['title']} (ID: {due_date_column['id']})")
        
        return board
        
    except Exception as e:
        print(f"❌ Error creating sample board: {e}")
        return None


def create_sample_item_with_subitems(client, board_id):
    """Create a sample item with subitems."""
    print("\nCreating sample item with subitems...")
    
    try:
        # Create main item
        main_item = client.create_item(
            board_id,
            "Sample Product",
            {
                "text": "Sample Style",
                "text1": "Sample Color",
                "text2": "High",
                "text3": "In Progress"
            }
        )
        print(f"✅ Created main item: {main_item['name']} (ID: {main_item['id']})")
        
        # Create subitems with due dates
        subitems = [
            {"name": "Fabric Approved", "due_date": "2024-03-15"},
            {"name": "Design Approved", "due_date": "2024-04-01"},
            {"name": "Production Approved", "due_date": "2024-05-01"}
        ]
        
        for subitem in subitems:
            subitem_data = client.create_subitem(
                main_item['id'],
                subitem['name'],
                {
                    "status": "Not Started",
                    "date": subitem['due_date']
                }
            )
            print(f"  ✅ Created subitem: {subitem_data['name']} (Due: {subitem['due_date']})")
        
        return main_item
        
    except Exception as e:
        print(f"❌ Error creating sample item: {e}")
        return None


def main():
    """Main setup function."""
    print("Welcome to Monday.com API Setup!")
    print("This script will help you set up and test your Monday.com API integration.")
    print()
    
    # Check if API token already exists
    api_token = os.environ.get('MONDAY_API_TOKEN')
    
    if not api_token:
        # Try to load from config file
        try:
            with open('monday_api_config.json', 'r') as f:
                config = json.load(f)
                api_token = config.get('api_token')
        except FileNotFoundError:
            pass
    
    if not api_token:
        api_token = setup_api_token()
        if not api_token:
            return
    
    # Test API connection
    if not test_api_connection(api_token):
        return
    
    # Ask if user wants to create a sample board
    create_sample = input("\nWould you like to create a sample board for testing? (y/n): ").lower().strip()
    
    if create_sample == 'y':
        client = MondayAPIClient(api_token)
        
        # Create sample board
        board = create_sample_board(client)
        if board:
            # Create sample item with subitems
            create_sample_item_with_subitems(client, board['id'])
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Run 'python monday_subitem_manager.py' to process your CSV data")
    print("2. Make sure your CSV files are in the same directory")
    print("3. Update the API token in the script if needed")


if __name__ == "__main__":
    main()

