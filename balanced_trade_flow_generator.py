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
    
    total_export = sum(export_data.values())
    total_import = sum(import_data.values())
    print(f"  Total export: {total_export}, Total import: {total_import}")
    
    # Prioritize both export and import constraints equally
    # We cannot satisfy both constraints exactly if total export ≠ total import
    # So our approach is to create a balanced allocation that preserves proportions
    
    results = []
    
    # Use a two-phase algorithm:
    # 1. Initial allocation based on proportions
    # 2. Adjustments to satisfy constraints exactly
    
    # Phase 1: Initial allocation
    # Create a matrix of trade flows, initially all zeros
    trade_matrix = {}
    for exporter in export_data.keys():
        trade_matrix[exporter] = {importer: 0 for importer in import_data.keys()}
    
    # For each exporter, allocate amounts to importers based on importer's share of total imports
    for exporter, export_amount in export_data.items():
        for importer, import_amount in import_data.items():
            # Calculate proportion of total imports that this importer represents
            import_proportion = import_amount / total_import
            
            # Allocate a proportional amount of this exporter's exports to this importer
            allocated_amount = int(export_amount * import_proportion)
            trade_matrix[exporter][importer] = allocated_amount
    
    # Phase 2: Adjustment to exactly match export constraints
    # Check how much we allocated for each exporter
    exporter_totals = {
        exporter: sum(trade_matrix[exporter].values())
        for exporter in export_data.keys()
    }
    
    # Adjust each exporter's allocations to match exactly what they should export
    for exporter, allocated_total in exporter_totals.items():
        target_total = export_data[exporter]
        if allocated_total != target_total:
            adjustment = target_total - allocated_total
            
            # Distribute the adjustment across importers
            # Start with the largest importers and work down
            sorted_importers = sorted(
                import_data.keys(), 
                key=lambda imp: trade_matrix[exporter][imp], 
                reverse=True
            )
            
            while adjustment != 0:
                for importer in sorted_importers:
                    # Adjust by one unit at a time
                    change = 1 if adjustment > 0 else -1
                    
                    # Ensure we don't create negative values
                    if change < 0 and trade_matrix[exporter][importer] < abs(change):
                        continue
                    
                    trade_matrix[exporter][importer] += change
                    adjustment -= change
                    
                    if adjustment == 0:
                        break
    
    # Convert the trade matrix to a list of trade flows
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
    
    # Convert to dataframe
    flow_df = pd.DataFrame(results)
    
    # Verify export constraints are exactly met
    if not flow_df.empty:
        export_sums = flow_df.groupby('Exporter')['Quantity'].sum()
        for exporter, expected in export_data.items():
            if exporter in export_sums:
                actual = export_sums[exporter]
                if actual != expected:
                    print(f"  ERROR: Export constraint not met for {exporter}: {actual} vs {expected}")
    
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
    
    # Check import constraint - we cannot match this exactly if total import ≠ total export
    print("\nChecking import totals (not expecting exact matches):")
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
                        if abs(import_totals[importer] - original_amount) / original_amount < 0.05:  # Within 5%
                            import_matches += 1
                        else:
                            diff = import_totals[importer] - original_amount
                            pct_diff = diff / original_amount * 100
                            print(f"  Year {year}, Importer {importer}: Synthetic {import_totals[importer]} vs Original {original_amount}, Diff: {diff} ({pct_diff:.2f}%)")
    
    print(f"Import totals within 5% of original: {import_matches}/{import_total} ({import_matches/import_total*100:.2f}%)")
    
    # Print summary statistics
    print(f"\nTotal records: {len(combined_flows)}")
    print(f"Years covered: {len(combined_flows['Year'].unique())}")
    print(f"Exporting countries: {len(combined_flows['Exporter'].unique())}")
    print(f"Importing countries: {len(combined_flows['Importer'].unique())}")
else:
    print("No data generated.")