import csv
from datetime import datetime


# Function to reorder the CSV by the Timestamp
def reorder_csv_by_timestamp(input_file, output_file):
    # Read the CSV file and store all rows in a list
    with open(input_file, mode="r", newline="") as infile:
        reader = csv.reader(infile)
        # Skip the header row
        header = next(reader)
        # Read the rest of the data
        rows = [row for row in reader]

    # Sort the rows based on the Timestamp column (first column, index 0)
    rows.sort(key=lambda x: datetime.strptime(x[0], "%Y-%m-%d %H:%M:%S"))

    # Write the sorted data to the output CSV file
    with open(output_file, mode="w", newline="") as outfile:
        writer = csv.writer(outfile)
        # Write the header
        writer.writerow(header)
        # Write the sorted rows
        writer.writerows(rows)


# Example usage
input_csv = "bar.csv"  # Your input file
output_csv = "sorted_ohlc_data.csv"  # Your desired output file with sorted data

reorder_csv_by_timestamp(input_csv, output_csv)
