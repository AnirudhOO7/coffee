import pandas as pd
import numpy as np
import random
import time
from collections import defaultdict

# Load datasets
export_df = pd.read_csv('Coffee_export.csv')
import_df = pd.read_csv('Coffee_import.csv')

# Clean the data - replace -2147483648 with NaN and convert to numeric
export_df = export_df.replace(-2147483648, np.nan)
for col in export_df.columns[1:-1]:  # Skip country name and total column
    export_df[col] = pd.to_numeric(export_df[col], errors='coerce')

for col in import_df.columns[1:-1]:  # Skip country name and total column
    import_df[col] = pd.to_numeric(import_df[col], errors='coerce')

# Function to generate synthetic trade flows for a specific year
def generate_trade_flows(year):
    start_time = time.time()
    if year not in export_df.columns or year not in import_df.columns:
        print(f"Year {year} not found in datasets")
        return None
    
    print(f"  Processing data for {year}...")
    
    # Get exporting and importing countries and their quantities for the year
    exporters = export_df[['Country', year]].dropna()
    importers = import_df[['Country', year]].dropna()
    
    # Filter out entries with -2147483648 which indicates missing data
    exporters = exporters[exporters[year] != -2147483648]
    importers = importers[importers[year] != -2147483648]
    
    # Strip whitespace from country names
    exporters['Country'] = exporters['Country'].str.strip()
    importers['Country'] = importers['Country'].str.strip()
    
    print(f"  Working with {len(exporters)} exporters and {len(importers)} importers")
    
    # Create a dataframe to store results
    columns = ['Exporter', 'Importer', 'Year', 'Quantity']
    trade_flows = []
    
    # Track remaining import/export quantities
    remaining_exports = exporters.set_index('Country')[year].to_dict()
    remaining_imports = importers.set_index('Country')[year].to_dict()
    
    # To ensure exact matching of totals, we'll use a constrained assignment approach
    while sum(remaining_exports.values()) > 0 and sum(remaining_imports.values()) > 0:
        # Select exporters and importers with remaining quantities
        active_exporters = {k: v for k, v in remaining_exports.items() if v > 0}
        active_importers = {k: v for k, v in remaining_imports.items() if v > 0}
        
        if not active_exporters or not active_importers:
            break
        
        # Pick exporter with most remaining quantity to distribute
        exporter = max(active_exporters.items(), key=lambda x: x[1])[0]
        exporter_remaining = remaining_exports[exporter]
        
        # Determine how to distribute this exporter's coffee
        # Strategy: Distribute proportionally to importers' remaining needs
        total_import_need = sum(active_importers.values())
        
        for importer, importer_remaining in list(active_importers.items()):
            # Skip if either has no remaining quantity
            if exporter_remaining <= 0 or importer_remaining <= 0:
                continue
            
            # Calculate proportional share, but limited by both constraints
            proportion = importer_remaining / total_import_need
            ideal_quantity = min(exporter_remaining * proportion, importer_remaining)
            
            # Ensure we don't assign fractional quantities - round to whole numbers
            # For the last assignments, we need to ensure exact totals
            if exporter_remaining <= ideal_quantity * 1.5 or importer_remaining <= ideal_quantity * 1.5:
                assigned_quantity = min(exporter_remaining, importer_remaining)
            else:
                assigned_quantity = ideal_quantity
            
            assigned_quantity = max(0, min(exporter_remaining, importer_remaining, assigned_quantity))
            
            if assigned_quantity > 0:
                # Add to trade flows - ensure we use integer values
                assigned_quantity_int = int(round(assigned_quantity))
                if assigned_quantity_int > 0:  # Only add if quantity is positive
                    trade_flows.append([exporter, importer, year, assigned_quantity_int])
                    
                    # Update remaining quantities
                    remaining_exports[exporter] -= assigned_quantity_int
                    remaining_imports[importer] -= assigned_quantity_int
                    exporter_remaining -= assigned_quantity_int
    
    # Final pass to allocate any small remaining amounts exactly
    # This ensures we match totals perfectly
    active_exporters = {k: v for k, v in remaining_exports.items() if v > 0}
    active_importers = {k: v for k, v in remaining_imports.items() if v > 0}
    
    # Handle any remaining export quantities
    for exporter, remaining in list(active_exporters.items()):
        if remaining > 0 and active_importers:
            # Distribute remaining export among importers with capacity
            importers_list = list(active_importers.keys())
            
            # Try to assign to a single importer if possible
            assigned = False
            for importer in importers_list:
                if remaining <= remaining_imports[importer]:
                    remaining_int = int(round(remaining))
                    if remaining_int > 0:
                        trade_flows.append([exporter, importer, year, remaining_int])
                        remaining_imports[importer] -= remaining_int
                        if remaining_imports[importer] <= 0:
                            active_importers.pop(importer)
                        assigned = True
                    break
            
            # If we couldn't assign to one importer, distribute proportionally
            if not assigned and importers_list:
                while remaining > 0 and importers_list:
                    importer = random.choice(importers_list)
                    quantity = min(remaining, remaining_imports[importer])
                    if quantity > 0:
                        quantity_int = int(round(quantity))
                        if quantity_int > 0:
                            trade_flows.append([exporter, importer, year, quantity_int])
                            remaining -= quantity_int
                            remaining_imports[importer] -= quantity_int
                            if remaining_imports[importer] <= 0:
                                importers_list.remove(importer)
                                active_importers.pop(importer)
    
    # Convert to dataframe
    flows_df = pd.DataFrame(trade_flows, columns=columns)
    
    # Verify constraints
    export_totals = flows_df.groupby('Exporter')['Quantity'].sum()
    import_totals = flows_df.groupby('Importer')['Quantity'].sum()
    
    export_diffs = export_totals - exporters.set_index('Country')[year]
    import_diffs = import_totals - importers.set_index('Country')[year]
    
    # Print verification
    print(f"Year {year} verification:")
    print(f"Export constraint: Max difference = {export_diffs.abs().max()}")
    print(f"Import constraint: Max difference = {import_diffs.abs().max()}")
    
    return flows_df

# Example usage for a specific year
def main():
    print("Starting synthetic coffee trade flow generation...")
    print("This will create trade flows for all countries from 1990-2019")
    # Generate trade flows for multiple years (start with fewer years for testing)
    years = [str(year) for year in range(1990, 1995)]  # 1990-1994 for testing
    
    all_flows = []
    for year in years:
        print(f"\nProcessing year {year}...")
        yearly_flows = generate_trade_flows(year)
        if yearly_flows is not None:
            all_flows.append(yearly_flows)
    
    # Combine all years
    if all_flows:
        combined_flows = pd.concat(all_flows)
        
        # Round quantities to integers and convert to int
        combined_flows['Quantity'] = combined_flows['Quantity'].round().astype(int)
        
        # Save to CSV
        output_file = 'synthetic_coffee_trade_flows.csv'
        combined_flows.to_csv(output_file, index=False)
        print(f"\nSynthetic trade flow data saved to {output_file}")
        
        # Print summary
        print(f"Total records generated: {len(combined_flows)}")
        print(f"Years covered: {combined_flows['Year'].unique()}")
        print(f"Exporting countries: {combined_flows['Exporter'].nunique()}")
        print(f"Exporter countries list: {sorted(combined_flows['Exporter'].unique())}")
        print(f"Importing countries: {combined_flows['Importer'].nunique()}")
        print(f"Importer countries list: {sorted(combined_flows['Importer'].unique())}")
        
        # Verify all countries from original datasets are included
        original_exporters = set(export_df['Country'].str.strip())
        original_importers = set(import_df['Country'].str.strip())
        
        synthetic_exporters = set(combined_flows['Exporter'])
        synthetic_importers = set(combined_flows['Importer'])
        
        missing_exporters = original_exporters - synthetic_exporters
        missing_importers = original_importers - synthetic_importers
        
        if missing_exporters:
            print(f"\nWARNING: Missing exporter countries: {missing_exporters}")
            # Add missing exporters with zero trades to ensure all countries appear
            for exporter in missing_exporters:
                if len(synthetic_importers) > 0:
                    importer = list(synthetic_importers)[0]  # Pick first importer
                    for year in years:
                        combined_flows = combined_flows.append({
                            'Exporter': exporter,
                            'Importer': importer,
                            'Year': year,
                            'Quantity': 0
                        }, ignore_index=True)
        
        if missing_importers:
            print(f"\nWARNING: Missing importer countries: {missing_importers}")
            # Add missing importers with zero trades
            for importer in missing_importers:
                if len(synthetic_exporters) > 0:
                    exporter = list(synthetic_exporters)[0]  # Pick first exporter
                    for year in years:
                        combined_flows = combined_flows.append({
                            'Exporter': exporter,
                            'Importer': importer,
                            'Year': year,
                            'Quantity': 0
                        }, ignore_index=True)
        
        # If we added missing countries, save the updated file
        if missing_exporters or missing_importers:
            combined_flows.to_csv(output_file, index=False)
            print(f"Updated file with all countries included")

if __name__ == "__main__":
    main()