import pandas as pd
import matplotlib.pyplot as plt
import re
import os

def generate_progress_graphs(log_file_path, output_dir):
    with open(log_file_path, 'r') as f:
        content = f.read()

    # Extract the table content
    # Assuming the table starts with a header and a separator line
    match = re.search(r'\| Date\s*\|\s*Weight \(lbs\)\s*\|\s*Body Fat %\s*\|\s*Notes\s*\|\s*\n\|(?: *:[-=]+\s*\|)+\n((?:\|.*?\n)*\|.*)', content)
    
    if not match:
        print("No data table found in the log file.")
        return

    table_string = match.group(1)
    print(f"Table string:\n{table_string}")
    
    # Read the table into a list of lists, then into a pandas DataFrame
    data = []
    for line in table_string.strip().split('\n'):
        # Split by '|' and strip whitespace, removing the first and last empty strings
        row = [item.strip() for item in line.split('|') if item.strip()]
        if row: # Ensure row is not empty
            data.append(row)

    print(f"Parsed data:\n{data}")
    if not data:
        print("No data found after parsing the table.")
        return

    df = pd.DataFrame(data, columns=['Date', 'Weight (lbs)', 'Body Fat %', 'Notes'])

    # Convert 'Date' to datetime objects
    df['Date'] = pd.to_datetime(df['Date'])
    # Convert 'Weight (lbs)' and 'Body Fat %' to numeric, handling potential errors
    df['Weight (lbs)'] = pd.to_numeric(df['Weight (lbs)'], errors='coerce')
    df['Body Fat %'] = pd.to_numeric(df['Body Fat %'], errors='coerce')

    # Drop rows where key numeric data is missing
    df.dropna(subset=['Weight (lbs)', 'Body Fat %'], inplace=True)

    if df.empty:
        print("No valid numeric data to plot after cleaning.")
        return

    # Sort by date to ensure correct plotting
    df.sort_values('Date', inplace=True)

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Plot Weight over Time
    plt.figure(figsize=(10, 6))
    plt.plot(df['Date'], df['Weight (lbs)'], marker='o')
    plt.title('Weight Over Time')
    plt.xlabel('Date')
    plt.ylabel('Weight (lbs)')
    plt.grid(True)
    plt.tight_layout()
    weight_chart_path = os.path.join(output_dir, 'weight_chart.png')
    plt.savefig(weight_chart_path)
    plt.close()
    print(f"Weight chart saved to {weight_chart_path}")

    # Plot Body Fat % over Time
    plt.figure(figsize=(10, 6))
    plt.plot(df['Date'], df['Body Fat %'], marker='o', color='red')
    plt.title('Body Fat Percentage Over Time')
    plt.xlabel('Date')
    plt.ylabel('Body Fat %')
    plt.grid(True)
    plt.tight_layout()
    bodyfat_chart_path = os.path.join(output_dir, 'bodyfat_chart.png')
    plt.savefig(bodyfat_chart_path)
    plt.close()
    print(f"Body Fat chart saved to {bodyfat_chart_path}")

    return weight_chart_path, bodyfat_chart_path

if __name__ == "__main__":
    log_file = 'Health_and_Fitness/check-in-log.md'
    output_directory = 'Health_and_Fitness/generated_html'
    
    # Ensure the script is run from the project root
    # This is a safeguard if the script is called directly, but the agent will handle paths
    if not os.path.exists(log_file):
        # Adjust path if running from scripts directory
        if os.path.exists(os.path.join('..', log_file)):
            log_file = os.path.join('..', log_file)
            output_directory = os.path.join('..', output_directory)
        else:
            print(f"Error: Log file not found at {log_file}")
            exit(1)

    generate_progress_graphs(log_file, output_directory)
