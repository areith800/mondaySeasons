#!/usr/bin/env python3
"""
Monday.com Board Generator

This script reads a master CSV file and configuration to generate department-specific
CSV files for Monday.com board import with sub-items and calculated due dates.
"""

import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import argparse


def load_config(config_file):
    """Load the configuration from JSON file."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)


def parse_launch_date(launch_date_str):
    """Parse launch date from various formats."""
    if not launch_date_str or launch_date_str.strip() == '':
        return None
    
    # Handle Excel serial date numbers (like 46062)
    try:
        if launch_date_str.isdigit():
            # Excel serial date (days since 1900-01-01, but Excel has a bug with leap year 1900)
            excel_date = int(launch_date_str)
            # Convert Excel serial date to Python date
            base_date = datetime(1899, 12, 30)  # Excel's epoch
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
    
    print(f"Warning: Could not parse launch date: {launch_date_str}")
    return None


def calculate_due_date(launch_date, lead_time_weeks):
    """Calculate due date by subtracting lead time from launch date."""
    if launch_date is None:
        return None
    
    due_date = launch_date - timedelta(weeks=lead_time_weeks)
    return due_date.strftime('%Y-%m-%d')


def generate_department_csv(master_data, config, department_name):
    """Generate CSV for a specific department."""
    if department_name not in config['departments']:
        print(f"Error: Department '{department_name}' not found in configuration.")
        return None
    
    dept_config = config['departments'][department_name]
    settings = config['settings']
    
    # Prepare CSV data
    csv_data = []
    
    for row in master_data:
        # Skip empty rows or header rows
        if not row or not row.get(settings['item_name_column']):
            continue
        
        # Skip rows that don't have launch dates
        launch_date_str = row.get(settings['launch_date_column'], '')
        launch_date = parse_launch_date(launch_date_str)
        
        if launch_date is None:
            continue
        
        # Create main item row
        main_item = {
            'Item': row.get(settings['item_name_column'], ''),
            'Style Name': row.get(settings['style_name_column'], ''),
            'Color Name': row.get(settings['color_name_column'], ''),
            'Priority': row.get(settings['priority_column'], ''),
            'Status': row.get(settings['status_column'], ''),
            'Platform': row.get(settings['platform_column'], ''),
            'Launch Date': launch_date.strftime('%Y-%m-%d'),
            'Type': 'Main Item'
        }
        csv_data.append(main_item)
        
        # Add sub-items
        for sub_item in dept_config['sub_items']:
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
                'Type': 'Sub Item',
                'Description': sub_item.get('description', '')
            }
            csv_data.append(sub_item_row)
    
    return csv_data


def write_csv(data, filename):
    """Write data to CSV file."""
    if not data:
        print(f"No data to write for {filename}")
        return
    
    fieldnames = data[0].keys()
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Generated {filename} with {len(data)} rows")


def main():
    parser = argparse.ArgumentParser(description='Generate Monday.com department boards from master CSV')
    parser.add_argument('master_csv', help='Path to master CSV file')
    parser.add_argument('config', help='Path to configuration JSON file')
    parser.add_argument('--department', help='Specific department to generate (default: all)')
    parser.add_argument('--output-dir', default='.', help='Output directory for generated CSV files')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Read master CSV
    try:
        with open(args.master_csv, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            master_data = list(reader)
    except FileNotFoundError:
        print(f"Error: Master CSV file '{args.master_csv}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading master CSV: {e}")
        sys.exit(1)
    
    print(f"Loaded {len(master_data)} rows from master CSV")
    
    # Generate CSV for specified department or all departments
    if args.department:
        departments = [args.department]
    else:
        departments = list(config['departments'].keys())
    
    for dept_name in departments:
        print(f"\nGenerating {dept_name} board...")
        csv_data = generate_department_csv(master_data, config, dept_name)
        
        if csv_data:
            # Create output filename
            safe_name = dept_name.replace(' ', '_').lower()
            output_file = Path(args.output_dir) / f"{safe_name}_board.csv"
            write_csv(csv_data, output_file)
        else:
            print(f"No data generated for {dept_name}")


if __name__ == "__main__":
    main()
