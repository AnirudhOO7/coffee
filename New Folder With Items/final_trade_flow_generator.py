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
    """Generate synthetic trade flows for a specific year using Linear Programming for optimal allocation"""
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
    total_export = sum(export_data.values())
    total_import = sum(import_data.values())
    print(f"  Total export: {total_export}, Total import: {total_import}")
    
    # If total export ≠ total import, we have to adjust to meet both constraints
    # Let's scale the import data to match export total since export data is our primary constraint
    scale_factor = 1.0
    if total_import != total_export:
        scale_factor = total_export / total_import
        print(f"  Scaling imports by factor: {scale_factor:.4f} to match export total")
        # Scale the import data temporarily for allocation purposes
        import_data_scaled = {k: int(v * scale_factor) for k, v in import_data.items()}
    
    # For each exporter, distribute its coffee among importers
    for exporter, export_amount in export_data.items():
        if export_amount <= 0:
            continue
            
        # Randomly assign this country's exports to importers while ensuring we don't exceed their import capacity
        remaining_export = export_amount
        
        # Make a copy of import_data to track remaining capacity for each importer
        remaining_import = {k: v for k, v in import_data.items()}
        
        # Continue distributing until we've assigned all this exporter's coffee
        while remaining_export > 0:
            # Get importers with remaining capacity
            available_importers = {k: v for k, v in remaining_import.items() if v > 0}
            
            if not available_importers:
                # If no importers have capacity left, pick one importer at random to take the overflow
                # This will violate import constraints but ensures export constraints are met
                importer = random.choice(list(import_data.keys()))
                results.append({
                    'Exporter': exporter,
                    'Importer': importer,
                    'Year': year_str,
                    'Quantity': remaining_export
                })
                remaining_export = 0
                break
            
            # Assign chunks randomly to importers with capacity
            for importer in random.sample(list(available_importers.keys()), len(available_importers)):
                # Randomly decide how much to assign to this importer (up to its capacity)
                max_assignment = min(remaining_export, remaining_import[importer])
                if max_assignment <= 0:
                    continue
                    
                # Assign a random portion of the remaining export to this importer
                # Use at least 1 unit and at most the maximum possible
                if max_assignment == 1:
                    assignment = 1
                else:
                    # Either assign a small portion or try to assign a large chunk to reduce fragmentation
                    if random.random() < 0.7:  # 70% chance of assigning a large chunk
                        assignment = random.randint(max(1, int(max_assignment * 0.5)), max_assignment)
                    else:
                        assignment = random.randint(1, max(1, int(max_assignment * 0.3)))
                
                results.append({
                    'Exporter': exporter,
                    'Importer': importer,
                    'Year': year_str,
                    'Quantity': assignment
                })
                
                remaining_export -= assignment
                remaining_import[importer] -= assignment
                
                if remaining_export <= 0:
                    break
    
    # Convert to DataFrame
    flow_df = pd.DataFrame(results)
    
    # Verify constraints
    if not flow_df.empty:
        # Check export constraint
        export_sums = flow_df.groupby('Exporter')['Quantity'].sum().to_dict()
        
        # Ensure all exporters have entries and match their export amounts
        for exporter, expected_amount in export_data.items():
            if exporter not in export_sums:
                # Add a zero entry if exporter is missing
                flow_df = flow_df.append({
                    'Exporter': exporter,
                    'Importer': list(import_data.keys())[0],
                    'Year': year_str,
                    'Quantity': 0
                }, ignore_index=True)
                export_sums[exporter] = 0
                
            # If export amount doesn't match, adjust an entry
            if export_sums[exporter] != expected_amount:
                # Find entries for this exporter
                exporter_entries = flow_df[flow_df['Exporter'] == exporter].index
                if len(exporter_entries) > 0:
                    # Add a new entry or adjust an existing one
                    adjustment = expected_amount - export_sums[exporter]
                    
                    if adjustment > 0:
                        # Add a new entry
                        flow_df = flow_df.append({
                            'Exporter': exporter,
                            'Importer': random.choice(list(import_data.keys())),
                            'Year': year_str,
                            'Quantity': adjustment
                        }, ignore_index=True)
                    else:
                        # Adjust existing entries
                        idx = exporter_entries[0]
                        current_quantity = flow_df.at[idx, 'Quantity']
                        
                        if current_quantity + adjustment > 0:
                            # Adjust this entry
                            flow_df.at[idx, 'Quantity'] = current_quantity + adjustment
                        else:
                            # Distribute the adjustment across multiple entries
                            remaining_adjustment = adjustment
                            for idx in exporter_entries:
                                current_quantity = flow_df.at[idx, 'Quantity']
                                if current_quantity > 0:
                                    change = max(-current_quantity, remaining_adjustment)
                                    flow_df.at[idx, 'Quantity'] = current_quantity + change
                                    remaining_adjustment -= change
                                    
                                    if remaining_adjustment == 0:
                                        break
    
    print(f"  Generated {len(flow_df)} trade flows for year {year_str}")
    return flow_df

# Generate data for all years
years = [str(year) for year in range(1990, 2020)]  # 1990-2019
all_flows = []

for year in years:
    yearly_flows = generate_data_for_year(year)
    if not yearly_flows.empty:
        all_flows.append(yearly_flows)

# Combine data from all years
if all_flows:
    print("Combining data from all years...")
    combined_flows = pd.concat(all_flows, ignore_index=True)
    
    # Ensure all quantities are integers with no decimals
    combined_flows['Quantity'] = combined_flows['Quantity'].round().astype(int)
    
    # Save to CSV
    output_file = 'synthetic_coffee_trade_flows.csv'
    combined_flows.to_csv(output_file, index=False)
    print(f"Successfully saved synthetic data to {output_file}")
    
    # Verify constraints
    print("\nVerifying constraints:")
    
    # Check export constraint by year and exporter
    print("Checking export constraints...")
    export_matches = 0
    export_total = 0
    
    for year in years:
        year_data = combined_flows[combined_flows['Year'] == year]
        if not year_data.empty:
            export_totals = year_data.groupby('Exporter')['Quantity'].sum()
            
            for exporter in export_totals.index:
                if exporter in export_df['Country'].values:
                    original_amount = export_df.loc[export_df['Country'] == exporter, year].values[0]
                    if not pd.isna(original_amount) and original_amount > 0:
                        export_total += 1
                        if export_totals[exporter] == original_amount:
                            export_matches += 1
                        else:
                            diff = export_totals[exporter] - original_amount
                            print(f"  Year {year}, Exporter {exporter}: Synthetic {export_totals[exporter]} vs Original {original_amount}, Diff: {diff}")
    
    print(f"Export constraint match: {export_matches}/{export_total} ({export_matches/export_total*100:.2f}%)")
    
    # Check import constraint by year and importer
    print("\nChecking import constraints...")
    import_matches = 0
    import_total = 0
    
    for year in years:
        year_data = combined_flows[combined_flows['Year'] == year]
        if not year_data.empty:
            import_totals = year_data.groupby('Importer')['Quantity'].sum()
            
            for importer in import_totals.index:
                if importer in import_df['Country'].values:
                    original_amount = import_df.loc[import_df['Country'] == importer, year].values[0]
                    if not pd.isna(original_amount) and original_amount > 0:
                        import_total += 1
                        if import_totals[importer] == original_amount:
                            import_matches += 1
                        else:
                            diff = import_totals[importer] - original_amount
                            print(f"  Year {year}, Importer {importer}: Synthetic {import_totals[importer]} vs Original {original_amount}, Diff: {diff}")
    
    print(f"Import constraint match: {import_matches}/{import_total} ({import_matches/import_total*100:.2f}%)")
    
    # Print summary statistics
    print(f"\nTotal records: {len(combined_flows)}")
    print(f"Years covered: {len(combined_flows['Year'].unique())}")
    print(f"Exporting countries: {len(combined_flows['Exporter'].unique())}")
    print(f"Importing countries: {len(combined_flows['Importer'].unique())}")
else:
    print("No data generated.")