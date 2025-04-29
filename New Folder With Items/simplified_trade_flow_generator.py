import pandas as pd
import numpy as np
import random

# Load datasets
print("Loading datasets...")
export_df = pd.read_csv('Coffee_export.csv')
import_df = pd.read_csv('Coffee_import.csv')

# Clean the data
print("Cleaning data...")
export_df = export_df.replace(-2147483648, np.nan)
for col in export_df.columns[1:-1]:  # Skip country name and total column
    export_df[col] = pd.to_numeric(export_df[col], errors='coerce')

for col in import_df.columns[1:-1]:  # Skip country name and total column
    import_df[col] = pd.to_numeric(import_df[col], errors='coerce')

# Strip whitespace from country names
export_df['Country'] = export_df['Country'].str.strip()
import_df['Country'] = import_df['Country'].str.strip()

def generate_data_for_year(year_str):
    """Generate synthetic trade flows for a specific year"""
    print(f"Generating data for year {year_str}...")
    
    # Get exporting and importing countries and their quantities for the year
    exporters = export_df[['Country', year_str]].dropna()
    importers = import_df[['Country', year_str]].dropna()
    
    # Convert to dictionaries for easier processing
    export_data = {row['Country']: int(row[year_str]) for _, row in exporters.iterrows() if row[year_str] > 0}
    import_data = {row['Country']: int(row[year_str]) for _, row in importers.iterrows() if row[year_str] > 0}
    
    # Initialize results dataframe
    results = []
    
    # Debug info
    print(f"  Exporters: {len(export_data)} countries with total {sum(export_data.values())} units")
    print(f"  Importers: {len(import_data)} countries with total {sum(import_data.values())} units")
    
    # Create a matrix of trade flows - we'll adjust this matrix to satisfy constraints
    # Start with a simple allocation based on country sizes
    trade_matrix = {}
    
    for exporter in export_data.keys():
        trade_matrix[exporter] = {}
        for importer in import_data.keys():
            # Initialize with a simple allocation
            trade_matrix[exporter][importer] = 1  # Start with minimal trade
    
    # Ensure each exporter's total equals its export amount
    remaining_export = {exporter: amount for exporter, amount in export_data.items()}
    remaining_import = {importer: amount for importer, amount in import_data.items()}
    
    # Remove the initial allocations from remaining amounts
    for exporter in export_data.keys():
        for importer in import_data.keys():
            remaining_export[exporter] -= trade_matrix[exporter][importer]
            remaining_import[importer] -= trade_matrix[exporter][importer]
    
    # Now distribute the remaining amounts to satisfy constraints
    # First, assign exports proportionally to importers with remaining capacity
    for exporter in sorted(remaining_export.keys(), key=lambda x: remaining_export[x], reverse=True):
        if remaining_export[exporter] <= 0:
            continue
            
        total_remaining_import = sum(max(0, val) for val in remaining_import.values())
        if total_remaining_import <= 0:
            break
            
        for importer in sorted(remaining_import.keys(), key=lambda x: remaining_import[x], reverse=True):
            if remaining_import[importer] <= 0:
                continue
                
            # Calculate share based on relative import need
            share = remaining_import[importer] / total_remaining_import
            allocation = min(int(remaining_export[exporter] * share), remaining_import[importer])
            
            # Update the trade matrix and remaining amounts
            if allocation > 0:
                trade_matrix[exporter][importer] += allocation
                remaining_export[exporter] -= allocation
                remaining_import[importer] -= allocation
                
            if remaining_export[exporter] <= 0:
                break
    
    # If there are still remaining exports, assign them to importers that can take more
    for exporter in sorted(remaining_export.keys(), key=lambda x: remaining_export[x], reverse=True):
        if remaining_export[exporter] <= 0:
            continue
            
        # Find importers with capacity
        importers_with_capacity = [imp for imp, val in remaining_import.items() if val > 0]
        
        if not importers_with_capacity:
            # If no importer has capacity, adjust the largest importer
            largest_importer = max(import_data.items(), key=lambda x: x[1])[0]
            trade_matrix[exporter][largest_importer] += remaining_export[exporter]
            remaining_export[exporter] = 0
        else:
            # Distribute remaining exports to importers with capacity
            while remaining_export[exporter] > 0 and importers_with_capacity:
                for importer in importers_with_capacity:
                    allocation = min(remaining_export[exporter], remaining_import[importer])
                    if allocation > 0:
                        trade_matrix[exporter][importer] += allocation
                        remaining_export[exporter] -= allocation
                        remaining_import[importer] -= allocation
                        
                        if remaining_import[importer] <= 0:
                            importers_with_capacity.remove(importer)
                            
                    if remaining_export[exporter] <= 0:
                        break
    
    # Convert the trade matrix to the result format
    for exporter in export_data.keys():
        for importer in import_data.keys():
            quantity = trade_matrix[exporter][importer]
            if quantity > 0:
                results.append({
                    'Exporter': exporter,
                    'Importer': importer,
                    'Year': year_str,
                    'Quantity': quantity
                })
    
    # Create the DataFrame
    flow_df = pd.DataFrame(results)
    
    # Verify constraints
    verification_passed = True
    
    if not flow_df.empty:
        # Check export constraint
        export_sums = flow_df.groupby('Exporter')['Quantity'].sum()
        for exporter, expected_amount in export_data.items():
            if exporter in export_sums:
                actual_amount = export_sums[exporter]
                if actual_amount != expected_amount:
                    print(f"  WARNING: Export constraint not met for {exporter}: {actual_amount} vs {expected_amount}")
                    verification_passed = False
                    
        # Check import constraint
        import_sums = flow_df.groupby('Importer')['Quantity'].sum()
        for importer, expected_amount in import_data.items():
            if importer in import_sums:
                actual_amount = import_sums[importer]
                if actual_amount != expected_amount:
                    print(f"  WARNING: Import constraint not met for {importer}: {actual_amount} vs {expected_amount}")
                    verification_passed = False
    
    if verification_passed:
        print(f"  Verification passed for year {year_str}")
    else:
        print(f"  Verification failed for year {year_str}")
        
    return flow_df
    
    return flow_df

# Generate data for multiple years
years = [str(year) for year in range(1990, 2020)]  # 1990-2019
all_flows = []

for year in years:
    yearly_flows = generate_data_for_year(year)
    if not yearly_flows.empty:
        all_flows.append(yearly_flows)

# Combine data from all years
if all_flows:
    print("Combining data from all years...")
    combined_flows = pd.concat(all_flows)
    
    # Ensure all quantities are integers
    combined_flows['Quantity'] = combined_flows['Quantity'].astype(int)
    
    # Save to CSV
    output_file = 'synthetic_coffee_trade_flows.csv'
    combined_flows.to_csv(output_file, index=False)
    print(f"Successfully saved synthetic data to {output_file}")
    
    # Print summary statistics
    print(f"Total records: {len(combined_flows)}")
    print(f"Years covered: {len(combined_flows['Year'].unique())}")
    print(f"Exporting countries: {len(combined_flows['Exporter'].unique())}")
    print(f"Importing countries: {len(combined_flows['Importer'].unique())}")
else:
    print("No data generated.")