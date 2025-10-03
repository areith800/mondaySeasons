# Monday.com API Integration

A Python-based integration for Monday.com that duplicates items from a Master board to a Product Development board with automatic subitem creation and due date calculation.

## Features

- ✅ **Board Duplication**: Copy items from SS26 Master to SS26 Prod Dev board
- ✅ **Group Management**: Automatically create and organize items into proper groups
- ✅ **Subitem Creation**: Add subitems with calculated due dates based on lead times
- ✅ **Platform Field Copying**: Transfer platform information between boards
- ✅ **Launch Date Processing**: Handle Excel serial dates and standard date formats
- ✅ **Error Handling**: Robust error handling with detailed logging

## Project Structure

```
Monday SS26/
├── monday_api_client.py          # Core Monday.com API client
├── duplicate_master_to_proddev.py # Main duplication script
├── test_single_subitem.py        # Test script for API functionality
├── setup_monday_api.py           # Setup and configuration script
├── monday_config.json            # Configuration file for subitems and lead times
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Monday.com API Token

1. Go to [Monday.com](https://auth.monday.com/users/sign_in)
2. Sign in to your account
3. Go to your profile settings
4. Find the "API" section
5. Generate a new API token

### 3. Configure API Token

Update the API token in the scripts:

```python
API_TOKEN = "your_monday_api_token_here"
```

### 4. Run Setup (Optional)

```bash
python setup_monday_api.py
```

## Usage

### Duplicate Master Board to Prod Dev

```bash
python duplicate_master_to_proddev.py
```

This script will:
1. Find both SS26 Master and SS26 Prod Dev boards
2. Create groups: SS26 New Colors, SS26 New Styles, End of Life Products
3. Duplicate all items with proper group assignment
4. Add subitems with calculated due dates
5. Copy platform information

### Test API Connection

```bash
python test_single_subitem.py
```

## Configuration

The `monday_config.json` file contains:

- **Department configurations** with subitem definitions
- **Lead times** for due date calculations
- **Column mappings** for data transfer

Example subitem configuration:
```json
{
  "task_name": "Fabric Approved",
  "lead_time_weeks": 40,
  "description": "Fabric selection and approval process"
}
```

## API Methods

### MondayAPIClient

- `get_boards()` - Get all accessible boards
- `get_board_by_name(name)` - Find board by name
- `create_board(name, kind)` - Create new board
- `create_item(board_id, name, column_values)` - Create item
- `create_subitem(parent_id, name, column_values)` - Create subitem
- `get_board_columns(board_id)` - Get board columns

### MondayBoardDuplicator

- `duplicate_master_to_proddev()` - Main duplication function
- `parse_launch_date(date_str)` - Parse various date formats
- `calculate_due_date(launch_date, lead_time_weeks)` - Calculate due dates

## Error Handling

The scripts include comprehensive error handling for:
- API connection issues
- Invalid data formats
- Missing required fields
- Rate limiting protection
- Network timeouts

## Troubleshooting

### Common Issues

1. **API Token Invalid**
   - Verify your token is correct
   - Check token permissions

2. **Board Not Found**
   - Ensure board names match exactly
   - Check board visibility

3. **Column Errors**
   - Verify column types match
   - Check dropdown options

4. **Network Issues**
   - Check internet connection
   - Retry failed operations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for internal use. Please ensure compliance with Monday.com's API terms of service.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Monday.com API documentation
3. Test with the setup script first
