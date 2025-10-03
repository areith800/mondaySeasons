import csv
from datetime import datetime, timedelta

# Function to convert Excel serial date to Python date
def excel_to_date(excel_date):
    base_date = datetime(1899, 12, 30)
    return base_date + timedelta(days=excel_date)

# Function to calculate due date
def calculate_due_date(launch_date, weeks_before):
    return launch_date - timedelta(weeks=weeks_before)

# Product Development sub-items
sub_items = [
    ("Fabric Approved", 40),
    ("Design Approved", 26),
    ("Fit Approved", 18),
    ("Color Approved", 16),
    ("Production Approved", 12)
]

# Read the master CSV
rows = []
with open('SS26_Master_1759354670.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['Item'] and row['Launch Date'] and row['Launch Date'].isdigit():
            rows.append(row)

# Generate Product Development CSV
output_rows = []

for row in rows:
    # Convert launch date
    launch_date = excel_to_date(int(row['Launch Date']))
    
    # Add main item
    main_item = {
        'Item': row['Item'],
        'Style Name': row['Style Name'],
        'Color Name': row['Color Name'],
        'Priority': row['Priority'],
        'Status': row['Exec Status'],
        'Platform': row['Platform'],
        'Launch Date': launch_date.strftime('%Y-%m-%d'),
        'Type': 'Main Item'
    }
    output_rows.append(main_item)
    
    # Add sub-items
    for task_name, weeks_before in sub_items:
        due_date = calculate_due_date(launch_date, weeks_before)
        
        sub_item = {
            'Item': f"  {task_name}",
            'Style Name': '',
            'Color Name': '',
            'Priority': '',
            'Status': 'Not Started',
            'Platform': '',
            'Launch Date': '',
            'Due Date': due_date.strftime('%Y-%m-%d'),
            'Type': 'Sub Item'
        }
        output_rows.append(sub_item)

# Write the output CSV
with open('product_development_board.csv', 'w', newline='', encoding='utf-8') as f:
    if output_rows:
        fieldnames = output_rows[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

print(f"Generated product_development_board.csv with {len(output_rows)} rows")
