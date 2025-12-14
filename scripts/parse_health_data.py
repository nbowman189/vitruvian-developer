import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
import os

def parse_health_data(file_path):
    """
    Parses HealthKit XML data to extract weight and body fat percentage.

    Args:
        file_path (str): The path to the XML file.

    Returns:
        dict: A dictionary with dates as keys and another dictionary 
              with 'weight' and 'bodyfat' as keys.
    """
    data_by_date = defaultdict(lambda: {'weight': None, 'bodyfat': None})

    for event, elem in ET.iterparse(file_path, events=('end',)):
        if elem.tag == 'Record':
            record_type = elem.attrib.get('type')
            
            if record_type == 'HKQuantityTypeIdentifierBodyMass':
                date = datetime.strptime(elem.attrib['startDate'], '%Y-%m-%d %H:%M:%S %z').strftime('%Y-%m-%d')
                data_by_date[date]['weight'] = round(float(elem.attrib['value']), 2)
                
            elif record_type == 'HKQuantityTypeIdentifierBodyFatPercentage':
                date = datetime.strptime(elem.attrib['startDate'], '%Y-%m-%d %H:%M:%S %z').strftime('%Y-%m-%d')
                # Convert decimal to percentage and round
                data_by_date[date]['bodyfat'] = round(float(elem.attrib['value']) * 100, 2)

            # Clear the element to free up memory
            elem.clear()

    return data_by_date

def read_all_log_entries(log_file_path):
    """
    Reads all entries from the check-in log and returns a dictionary of entries by date.
    """
    all_entries = {}
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as f:
            # Skip header and separator lines
            lines = f.readlines()
            data_lines = lines[2:] # Assuming header and separator are first two lines

            for line in data_lines:
                if line.strip().startswith('| 20'):
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 4: # Ensure enough parts for date, weight, bodyfat
                        date_str = parts[1]
                        weight = float(parts[2]) if parts[2] != 'None' and parts[2] != 'N/A' else None
                        bodyfat = float(parts[3]) if parts[3] != 'None' and parts[3] != 'N/A' else None
                        all_entries[date_str] = {'weight': weight, 'bodyfat': bodyfat}
    return all_entries

def rewrite_log(log_file_path, sorted_entries):
    """
    Rewrites the check-in log file with sorted entries.
    """
    header = "| Date | Weight (lbs) | Body Fat % | Notes |\n"
    separator = "| :--------- | :----------- | :--------- | :---------------------------------- |\n"

    with open(log_file_path, 'w') as f:
        f.write(header)
        f.write(separator)
        for date, data in sorted_entries:
            weight = data.get('weight', 'N/A')
            bodyfat = data.get('bodyfat', 'N/A')
            f.write(f"| {date} | {weight} | {bodyfat} | |\n")

if __name__ == '__main__':
    xml_file_path = 'Health_and_Fitness/export.xml'
    log_file_path = 'Health_and_Fitness/check-in-log.md'

    # Parse new data from XML
    parsed_data = parse_health_data(xml_file_path)

    # Read all existing entries from the log
    all_existing_entries = read_all_log_entries(log_file_path)

    # Combine new and existing data, prioritizing new data if dates overlap
    combined_data = all_existing_entries.copy()
    for date, data in parsed_data.items():
        combined_data[date] = data

    # Sort combined data by date
    sorted_combined_entries = sorted(combined_data.items())

    # Rewrite the log file with sorted data
    rewrite_log(log_file_path, sorted_combined_entries)
    print(f"Successfully updated and sorted {len(sorted_combined_entries)} entries in {log_file_path}")
