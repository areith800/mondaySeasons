#!/usr/bin/env python3
"""
Monday.com API Client

This script provides functionality to interact with Monday.com API,
including creating boards, items, and subitems with due dates.
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time


class MondayAPIClient:
    """Monday.com API client for managing boards, items, and subitems."""
    
    def __init__(self, api_token: str):
        """
        Initialize the Monday.com API client.
        
        Args:
            api_token: Your Monday.com API token
        """
        self.api_token = api_token
        self.base_url = "https://api.monday.com/v2"
        self.headers = {
            "Authorization": api_token,
            "Content-Type": "application/json"
        }
    
    def _make_request(self, query: str, variables: Dict = None) -> Dict:
        """
        Make a GraphQL request to Monday.com API.
        
        Args:
            query: GraphQL query string
            variables: Variables for the query
            
        Returns:
            API response data
        """
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
    
    def get_boards(self) -> List[Dict]:
        """Get all boards accessible to the user."""
        query = """
        query {
            boards {
                id
                name
                state
                columns {
                    id
                    title
                    type
                }
            }
        }
        """
        
        data = self._make_request(query)
        return data.get("boards", [])
    
    def get_board_by_name(self, board_name: str) -> Optional[Dict]:
        """
        Find a board by name.
        
        Args:
            board_name: Name of the board to find
            
        Returns:
            Board data if found, None otherwise
        """
        boards = self.get_boards()
        for board in boards:
            if board["name"] == board_name:
                return board
        return None
    
    def create_board(self, board_name: str, board_kind: str = "private") -> Dict:
        """
        Create a new board.
        
        Args:
            board_name: Name of the board to create
            board_kind: Type of board (private, public, share)
            
        Returns:
            Created board data
        """
        query = """
        mutation($boardName: String!, $boardKind: BoardKind!) {
            create_board(board_name: $boardName, board_kind: $boardKind) {
                id
                name
            }
        }
        """
        
        variables = {
            "boardName": board_name,
            "boardKind": board_kind.upper()
        }
        
        data = self._make_request(query, variables)
        return data["create_board"]
    
    def get_board_columns(self, board_id: str) -> List[Dict]:
        """
        Get columns for a specific board.
        
        Args:
            board_id: ID of the board
            
        Returns:
            List of column data
        """
        query = """
        query($boardId: [ID!]!) {
            boards(ids: $boardId) {
                columns {
                    id
                    title
                    type
                    settings_str
                }
            }
        }
        """
        
        variables = {"boardId": [board_id]}
        data = self._make_request(query, variables)
        
        if data.get("boards"):
            return data["boards"][0]["columns"]
        return []
    
    def create_item(self, board_id: str, item_name: str, column_values: Dict = None) -> Dict:
        """
        Create a new item on a board.
        
        Args:
            board_id: ID of the board
            item_name: Name of the item
            column_values: Dictionary of column values
            
        Returns:
            Created item data
        """
        query = """
        mutation($boardId: ID!, $itemName: String!, $columnValues: JSON!) {
            create_item(board_id: $boardId, item_name: $itemName, column_values: $columnValues) {
                id
                name
            }
        }
        """
        
        variables = {
            "boardId": board_id,
            "itemName": item_name,
            "columnValues": json.dumps(column_values or {})
        }
        
        data = self._make_request(query, variables)
        return data["create_item"]
    
    def create_subitem(self, parent_item_id: str, subitem_name: str, column_values: Dict = None) -> Dict:
        """
        Create a subitem under a parent item.
        
        Args:
            parent_item_id: ID of the parent item
            subitem_name: Name of the subitem
            column_values: Dictionary of column values including due date
            
        Returns:
            Created subitem data
        """
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
    
    def get_items(self, board_id: str) -> List[Dict]:
        """
        Get all items from a board.
        
        Args:
            board_id: ID of the board
            
        Returns:
            List of item data
        """
        query = """
        query($boardId: [ID!]!) {
            boards(ids: $boardId) {
                items {
                    id
                    name
                    column_values {
                        id
                        text
                        value
                    }
                }
            }
        }
        """
        
        variables = {"boardId": [board_id]}
        data = self._make_request(query, variables)
        
        if data.get("boards"):
            return data["boards"][0]["items"]
        return []
    
    def find_item_by_name(self, board_id: str, item_name: str) -> Optional[Dict]:
        """
        Find an item by name on a board.
        
        Args:
            board_id: ID of the board
            item_name: Name of the item to find
            
        Returns:
            Item data if found, None otherwise
        """
        items = self.get_items(board_id)
        for item in items:
            if item["name"] == item_name:
                return item
        return None
    
    def add_due_date_column(self, board_id: str, column_title: str = "Due Date") -> Dict:
        """
        Add a due date column to a board.
        
        Args:
            board_id: ID of the board
            column_title: Title for the due date column
            
        Returns:
            Created column data
        """
        query = """
        mutation($boardId: ID!, $columnTitle: String!) {
            create_column(board_id: $boardId, title: $columnTitle, column_type: date) {
                id
                title
            }
        }
        """
        
        variables = {
            "boardId": board_id,
            "columnTitle": column_title
        }
        
        data = self._make_request(query, variables)
        return data["create_column"]
    
    def get_or_create_due_date_column(self, board_id: str, column_title: str = "Due Date") -> str:
        """
        Get existing due date column or create one if it doesn't exist.
        
        Args:
            board_id: ID of the board
            column_title: Title for the due date column
            
        Returns:
            Column ID
        """
        columns = self.get_board_columns(board_id)
        
        # Look for existing due date column
        for column in columns:
            if column["title"] == column_title:
                return column["id"]
        
        # Create new due date column
        column_data = self.add_due_date_column(board_id, column_title)
        return column_data["id"]


def main():
    """Example usage of the Monday.com API client."""
    # You'll need to set your API token
    API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjU2OTEzMjQwMiwiYWFpIjoxMSwidWlkIjoyNTU3NDU5OSwiaWFkIjoiMjAyNS0xMC0wMVQyMzo0NTo0OC40NjRaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MzM3OTc2MywicmduIjoidXNlMSJ9.XCcD2sOVi5HP1o14pyD0Q8MFhJqBwlqFgKfC8UXpRMM"
    
    if API_TOKEN == "YOUR_MONDAY_API_TOKEN_HERE":
        print("Please set your Monday.com API token in the script")
        print("You can get your API token from: https://auth.monday.com/users/sign_in")
        return
    
    client = MondayAPIClient(API_TOKEN)
    
    try:
        # Example: Get all boards
        print("Fetching boards...")
        boards = client.get_boards()
        print(f"Found {len(boards)} boards")
        
        for board in boards:
            print(f"- {board['name']} (ID: {board['id']})")
        
        # Example: Create a new board
        # board_name = "Test Board"
        # board = client.create_board(board_name)
        # print(f"Created board: {board['name']} (ID: {board['id']})")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()

