#!/usr/bin/env python3
"""
Monday.com Subitem Manager

This script reads your existing CSV data and creates subitems on Monday.com boards
with calculated due dates based on your configuration.
"""

import csv
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from monday_api_client import MondayAPIClient


class MondaySubitemManager:
    """Manages subitems on Monday.com boards with due dates."""
    
    def __init__(self, api_token: str):
        """
        Initialize the subitem manager.
        
        Args:
            api_token: Your Monday.com API token
        """
        self.client = MondayAPIClient(api_token)
        self.due_date_column_id = None
    
    def parse_launch_date(self, launch_date_str: str) -> Optional[datetime]:
        """Parse launch date from various formats."""
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
        date_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S'
        ]
        
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
    
    def setup_board_for_subitems(self, board_id: str, due_date_column_title: str = "Due Date") -> str:
        """
        Ensure board has a due date column and return its ID.
        
        Args:
            board_id: ID of the board
            due_date_column_title: Title for the due date column
            
        Returns:
            Column ID for due dates
        """
        try:
            column_id = self.client.get_or_create_due_date_column(board_id, due_date_column_title)
            self.due_date_column_id = column_id
            print(f"Due date column '{due_date_column_title}' ready (ID: {column_id})")
            return column_id
        except Exception as e:
            print(f"Error setting up due date column: {e}")
            raise
    
    def create_main_item_with_subitems(self, board_id: str, item_data: Dict, subitems_config: List[Dict]) -> Dict:
        """
        Create a main item and its subitems with due dates.
        
        Args:
            board_id: ID of the board
            item_data: Main item data
            subitems_config: List of subitem configurations
            
        Returns:
            Created main item data
        """
        try:
            # Create main item
            main_item_name = item_data.get('Item', '')
            print(f"Creating main item: {main_item_name}")
            
            # Prepare column values for main item
            main_column_values = {
                'text': item_data.get('Style Name', ''),
                'text1': item_data.get('Color Name', ''),
                'text2': item_data.get('Priority', ''),
                'text3': item_data.get('Status', ''),
                'text4': item_data.get('Platform', ''),
                'date': item_data.get('Launch Date', '')
            }
            
            # Remove empty values
            main_column_values = {k: v for k, v in main_column_values.items() if v}
            
            main_item = self.client.create_item(board_id, main_item_name, main_column_values)
            print(f"Created main item: {main_item['name']} (ID: {main_item['id']})")
            
            # Create subitems
            launch_date = self.parse_launch_date(item_data.get('Launch Date', ''))
            if launch_date:
                for subitem_config in subitems_config:
                    subitem_name = subitem_config['task_name']
                    lead_time_weeks = subitem_config['lead_time_weeks']
                    
                    # Calculate due date
                    due_date = self.calculate_due_date(launch_date, lead_time_weeks)
                    
                    # Prepare column values for subitem
                    subitem_column_values = {
                        'status': 'Not Started'
                    }
                    
                    # Add due date if column is available
                    if self.due_date_column_id and due_date:
                        subitem_column_values[self.due_date_column_id] = due_date
                    
                    # Add description if available
                    if 'description' in subitem_config:
                        subitem_column_values['text'] = subitem_config['description']
                    
                    # Remove empty values
                    subitem_column_values = {k: v for k, v in subitem_column_values.items() if v}
                    
                    subitem = self.client.create_subitem(
                        main_item['id'],
                        subitem_name,
                        subitem_column_values
                    )
                    
                    print(f"  Created subitem: {subitem['name']} (Due: {due_date})")
            
            return main_item
            
        except Exception as e:
            print(f"Error creating item with subitems: {e}")
            raise
    
    def process_csv_data(self, csv_file: str, board_name: str, department_config: Dict):
        """
        Process CSV data and create items with subitems on Monday.com.
        
        Args:
            csv_file: Path to CSV file
            board_name: Name of the Monday.com board
            department_config: Department configuration from JSON
        """
        try:
            # Get or create board
            board = self.client.get_board_by_name(board_name)
            if not board:
                print(f"Creating new board: {board_name}")
                board = self.client.create_board(board_name)
            else:
                print(f"Using existing board: {board_name} (ID: {board['id']})")
            
            board_id = board['id']
            
            # Setup due date column
            self.setup_board_for_subitems(board_id)
            
            # Read CSV data
            csv_data = []
            with open(csv_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                csv_data = list(reader)
            
            print(f"Processing {len(csv_data)} rows from {csv_file}")
            
            # Process each main item
            main_items_created = 0
            for row in csv_data:
                # Skip subitems (they start with spaces)
                if row.get('Item', '').startswith('  '):
                    continue
                
                # Skip empty rows
                if not row.get('Item'):
                    continue
                
                # Only process main items
                if row.get('Type') == 'Main Item':
                    try:
                        self.create_main_item_with_subitems(
                            board_id,
                            row,
                            department_config['sub_items']
                        )
                        main_items_created += 1
                        
                        # Add small delay to avoid rate limiting
                        time.sleep(0.5)
                        
                    except Exception as e:
                        print(f"Error processing item {row.get('Item', 'Unknown')}: {e}")
                        continue
            
            print(f"Successfully created {main_items_created} main items with subitems")
            
        except Exception as e:
            print(f"Error processing CSV data: {e}")
            raise


def main():
    """Main function to run the subitem manager."""
    # Configuration
    API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjU2OTEzMjQwMiwiYWFpIjoxMSwidWlkIjoyNTU3NDU5OSwiaWFkIjoiMjAyNS0xMC0wMVQyMzo0NTo0OC40NjRaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MzM3OTc2MywicmduIjoidXNlMSJ9.XCcD2sOVi5HP1o14pyD0Q8MFhJqBwlqFgKfC8UXpRMM"
    
    if API_TOKEN == "YOUR_MONDAY_API_TOKEN_HERE":
        print("Please set your Monday.com API token in the script")
        print("You can get your API token from: https://auth.monday.com/users/sign_in")
        return
    
    # Load configuration
    try:
        with open('monday_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: monday_config.json not found")
        return
    
    # Initialize manager
    manager = MondaySubitemManager(API_TOKEN)
    
    # Process each department
    departments = config['departments']
    
    for dept_name, dept_config in departments.items():
        print(f"\n=== Processing {dept_name} ===")
        
        # Find corresponding CSV file
        csv_file = f"{dept_name.lower().replace(' ', '_')}_board.csv"
        
        try:
            manager.process_csv_data(
                csv_file,
                dept_config['board_name'],
                dept_config
            )
        except FileNotFoundError:
            print(f"CSV file {csv_file} not found, skipping {dept_name}")
        except Exception as e:
            print(f"Error processing {dept_name}: {e}")


if __name__ == "__main__":
    main()

