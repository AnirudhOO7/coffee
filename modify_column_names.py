import pandas as pd
import os

# Get the directory path
dir_path = os.path.dirname(os.path.realpath(__file__))

# Files to process
files_to_process = [
    os.path.join(dir_path, "Coffee_domestic_consumption.csv"),
    os.path.join(dir_path, "Coffee_production.csv")
]

for file_path in files_to_process:
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Get the column names
    columns = df.columns.tolist()
    
    # Create a mapping for the columns that need to be modified
    column_mapping = {}
    for col in columns:
        # Check if the column name has the pattern YYYY/YY
        if '/' in col and col[0:4].isdigit():
            # Extract only the first year (e.g., 1990 from 1990/91)
            first_year = col.split('/')[0]
            column_mapping[col] = first_year
    
    # Rename the columns
    df = df.rename(columns=column_mapping)
    
    # Save the modified CSV file
    modified_file_path = file_path.replace('.csv', '_modified.csv')
    df.to_csv(modified_file_path, index=False)
    print(f"Modified file saved as: {modified_file_path}")

print("Column renaming completed.")