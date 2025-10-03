#!/usr/bin/env python3
"""
Simple script to generate Product Development board CSV
"""

import csv
import json
from datetime import datetime, timedelta

def parse_launch_date(launch_date_str):
    """Parse launch date from Excel serial number or date string."""
    if not launch_date_str or launch_date_str.strip() == '':
        return None
    
    # Handle Excel serial date numbers (like 46062)
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

# Product Development sub-items
sub_items = [
    {"task_name": "Fabric Approved", "lead_time_weeks": 40},
    {"task_name": "Design Approved", "lead_time_weeks": 26},
    {"task_name": "Fit Approved", "lead_time_weeks": 18},
    {"task_name": "Color Approved", "lead_time_weeks": 16},
    {"task_name": "Production Approved", "lead_time_weeks": 12}
]

# Read master CSV
master_data = []
with open('SS26_Master_1759354670.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    master_data = list(reader)

print(f"Loaded {len(master_data)} rows from master CSV")

# Generate Product Development CSV
csv_data = []

for row in master_data:
    # Skip empty rows
    if not row.get('Item'):
        continue
    
    # Parse launch date
    launch_date_str = row.get('Launch Date', '')
    launch_date = parse_launch_date(launch_date_str)
    
    if launch_date is None:
        continue
    
    # Create main item row
    main_item = {
        'Item': row.get('Item', ''),
        'Style Name': row.get('Style Name', ''),
        'Color Name': row.get('Color Name', ''),
        'Priority': row.get('Priority', ''),
        'Status': row.get('Exec Status', ''),
        'Platform': row.get('Platform', ''),
        'Launch Date': launch_date.strftime('%Y-%m-%d'),
        'Type': 'Main Item'
    }
    csv_data.append(main_item)
    
    # Add sub-items
    for sub_item in sub_items:
        due_date = calculate_due_date(launch_date, sub_item['lead_time_weeks'])
        
        sub_item_row = {
            'Item': f"  {sub_item['task_name']}",
            'Style Name': '',
            'Color Name': '',
            'Priority': '',
            'Status': 'Not Started',
            'Platform': '',
            'Launch Date': '',
            'Due Date': due_date if due_date else '',
            'Type': 'Sub Item'
        }
        csv_data.append(sub_item_row)

# Write CSV
if csv_data:
    fieldnames = csv_data[0].keys()
    with open('product_development_board.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)
    
    print(f"Generated product_development_board.csv with {len(csv_data)} rows")
else:
    print("No data generated")
