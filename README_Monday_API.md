# Monday.com API Integration

This package provides tools to interact with the Monday.com API, specifically for creating boards, items, and subitems with due dates.

## Features

- ✅ Create and manage Monday.com boards
- ✅ Add items and subitems with due dates
- ✅ Process CSV data to create structured boards
- ✅ Automatic due date calculation based on lead times
- ✅ Error handling and logging

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Your Monday.com API Token

1. Go to [Monday.com](https://auth.monday.com/users/sign_in)
2. Sign in to your account
3. Go to your profile settings
4. Find the "API" section
5. Generate a new API token

### 3. Run the Setup Script

```bash
python setup_monday_api.py
```

This will:
- Help you configure your API token
- Test the connection to Monday.com
- Optionally create a sample board for testing

## Usage

### Basic API Client

```python
from monday_api_client import MondayAPIClient

# Initialize client
client = MondayAPIClient("YOUR_API_TOKEN")

# Get all boards
boards = client.get_boards()

# Create a new board
board = client.create_board("My New Board")

# Create an item
item = client.create_item(board['id'], "My Item", {
    "text": "Description",
    "status": "In Progress"
})

# Create a subitem with due date
subitem = client.create_subitem(item['id'], "My Subitem", {
    "status": "Not Started",
    "date": "2024-12-31"  # Due date
})
```

### Process CSV Data

```python
from monday_subitem_manager import MondaySubitemManager

# Initialize manager
manager = MondaySubitemManager("YOUR_API_TOKEN")

# Process your CSV data
manager.process_csv_data(
    "product_development_board.csv",
    "Product Development Board",
    department_config
)
```

### Full Integration

Run the main script to process all your department boards:

```bash
python monday_subitem_manager.py
```

This will:
1. Read your existing CSV files
2. Create or find Monday.com boards for each department
3. Add main items and subitems with calculated due dates
4. Handle errors gracefully

## Configuration

The script uses your existing `monday_config.json` file to determine:
- Department configurations
- Subitem definitions
- Lead times for due date calculations

## API Methods

### MondayAPIClient

- `get_boards()` - Get all accessible boards
- `get_board_by_name(name)` - Find board by name
- `create_board(name, kind)` - Create new board
- `create_item(board_id, name, column_values)` - Create item
- `create_subitem(parent_id, name, column_values)` - Create subitem
- `get_board_columns(board_id)` - Get board columns
- `add_due_date_column(board_id, title)` - Add due date column

### MondaySubitemManager

- `process_csv_data(csv_file, board_name, config)` - Process CSV and create items
- `create_main_item_with_subitems(board_id, item_data, subitems_config)` - Create item with subitems
- `setup_board_for_subitems(board_id)` - Ensure board has due date column

## Error Handling

The scripts include comprehensive error handling:
- API connection errors
- Invalid data format
- Missing required fields
- Rate limiting protection

## Examples

### Create a Board with Items and Subitems

```python
from monday_api_client import MondayAPIClient

client = MondayAPIClient("YOUR_API_TOKEN")

# Create board
board = client.create_board("Product Development")

# Add due date column
due_date_column = client.add_due_date_column(board['id'], "Due Date")

# Create main item
item = client.create_item(board['id'], "Product A", {
    "text": "Style Name",
    "text1": "Color"
})

# Create subitems with due dates
subitems = [
    ("Fabric Approved", "2024-03-15"),
    ("Design Approved", "2024-04-01"),
    ("Production Approved", "2024-05-01")
]

for subitem_name, due_date in subitems:
    client.create_subitem(item['id'], subitem_name, {
        "status": "Not Started",
        "date": due_date
    })
```

## Troubleshooting

### Common Issues

1. **API Token Invalid**
   - Make sure your token is correct
   - Check that the token has the right permissions

2. **Board Not Found**
   - The script will create boards if they don't exist
   - Check board names match exactly

3. **Column Errors**
   - The script automatically creates due date columns
   - Make sure your board has the right column types

4. **Rate Limiting**
   - The script includes delays to avoid rate limits
   - If you get rate limit errors, increase the delay

### Getting Help

- Check the Monday.com API documentation
- Verify your API token permissions
- Test with the setup script first
- Check the console output for specific error messages

## Next Steps

1. Run `python setup_monday_api.py` to get started
2. Test with a small dataset first
3. Process your full CSV data
4. Customize the scripts for your specific needs

