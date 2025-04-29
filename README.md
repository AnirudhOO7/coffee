# Coffee Dashboard

An interactive visualization dashboard for exploring global coffee production, consumption, import, export, and trade flow data from 1990 to 2019.

## Overview

This dashboard provides a comprehensive analysis of coffee market dynamics through interactive visualizations built with Dash and Plotly. The dashboard offers detailed insights into production patterns, consumption trends, import/export data, and global trade flows, allowing users to explore coffee market dynamics across different countries and years.

## Features

- **Production Analysis**: Explore coffee production by country, coffee type, and year
- **Consumption Analysis**: Analyze coffee consumption patterns across countries and time
- **Import Analysis**: Examine coffee import trends and top importing countries
- **Export Analysis**: View coffee export data by country and growth rates
- **Trade Flow Visualization**: Interactive Sankey diagram showing coffee trade flows between countries with filtering by exporter and importer

## Visualizations & Technical Details

### Common Features Across Tabs
- **Year Slider**: Interactive slider (1990-2019) using `dcc.Slider` for temporal filtering
- **Coffee Color Theme**: Custom color palette with `COFFEE_COLORS` and `COFFEE_COLORSCALE` variables

### Production Tab
1. **Treemap Chart**: Country-based production proportional visualization
   - Library: `plotly.express.treemap`
   - Data Source: `Coffee_production_modified.csv`
   - Technique: Hierarchical data segmentation by country with dynamic color scaling
   - Features: Interactive tooltips, zoom capability

2. **Countries Table**: Ranked list of producing countries
   - Implementation: Custom HTML table with `html.Table`, `html.Tr`, `html.Td` components
   - Styling: Alternating row colors, responsive layout
   - Data: Sorted by production volume using `sort_values` in pandas

3. **Radial/Pie Chart**: Top 10 producers visualization
   - Library: `plotly.express.pie` with hole parameter for donut effect
   - Features: "Others" category aggregation for non-top countries
   - Data Processing: `get_top_countries` helper function to extract top producers

4. **Trend Line Chart**: Production across years
   - Libraries: `plotly.graph_objects.Scatter` for line and markers
   - Technique: Polynomial fitting with `np.polyfit` for trend line
   - Data Processing: Aggregation with `get_annual_totals` function

5. **Coffee Types Bar Chart**: Production by coffee variety
   - Library: `plotly.graph_objects.Bar`
   - Data Processing: `get_coffee_type_totals` for categorization by Arabica, Robusta, and mixed varieties
   - Features: Value labels with formatted numbers

### Consumption Tab
Similar visualizations as Production tab, using `Coffee_domestic_consumption_modified.csv` with consumption-specific calculations and titles.

### Import Tab
1. **Treemap Chart**: Country-based import proportional visualization
   - Data Source: `Coffee_import.csv`
   - Implementation: Same technique as production treemap with import data

2. **Countries Table**: Ranked list of importing countries
   - Sorted by import volume using pandas

3. **Radial Chart**: Top 10 importers visualization
   - Same implementation as production but with import data

4. **Trend Line Chart**: Import volumes across years
   - Shows historical import patterns with trend line

### Export Tab
1. **Treemap Chart**: Country-based export proportional visualization
   - Data Source: `Coffee_export.csv` with special handling for missing/invalid values
   - Data Cleaning: `replace(-2147483648, np.nan)` to handle placeholder values

2. **Countries Table**: Ranked list of exporting countries
   - Implementation: Similar to import/production with export-specific data

3. **Radial Chart**: Top 10 exporters visualization
   - Data Processing: Includes filtering for NaN values with `dropna()`

4. **Trend Line Chart**: Export volumes across years
   - Features: Special handling for missing data in trend calculation with `fillna(0)`

### Trade Flow Tab
1. **Filter Dropdowns**: Country-specific filtering
   - Components: `dcc.Dropdown` for exporter and importer selection
   - Implementation: Dynamic filtering based on selection

2. **Sankey Diagram**: Flow visualization of trade connections
   - Library: `plotly.graph_objects.Sankey`
   - Data Source: `synthetic_coffee_trade_flows.csv`
   - Features: Node coloring by type (exporter/importer), dynamic sizing based on quantity

3. **Top Countries Tables**: Exporters and importers rankings
   - Implementation: Dynamic table generation based on filtered dataset

## Data Sources & Processing

The dashboard uses the following CSV data files:
- `Coffee_production_modified.csv`: Production volumes by country and coffee type
- `Coffee_domestic_consumption_modified.csv`: Consumption data by country
- `Coffee_import.csv`: Import volumes by country
- `Coffee_export.csv`: Export volumes by country (with special handling for -2147483648 values)
- `synthetic_coffee_trade_flows.csv`: Trade flow connections between countries

Data processing techniques used:
- Pandas operations: `groupby`, `sort_values`, `sum`, `dropna`, `replace`, `merge`
- NumPy functions: `polyfit`, `poly1d`, `isnan`, `percentile` 
- Custom helper functions:
  - `get_top_countries`: Extracts top N countries for a specified metric and year
  - `get_annual_totals`: Calculates yearly totals with optional coffee type filtering
  - `get_coffee_type_totals`: Segments data by coffee type (Arabica, Robusta, mixed)
  - `get_production_consumption_by_year`: Creates comparative yearly data

## Technologies Used

- **Dash**: Web application framework for creating interactive dashboards
- **Plotly**: Interactive visualization library
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computations and array operations
- **Python 3**: Core programming language

## Setup and Running
sed -i '' 's/\r$//' ./run_final_dashboard_fixes.sh
### Running the Dashboard
```bash
./run_final_dashboard_fixes.sh
```

Or directly with Python:
```bash
python coffee_dashboard_revised.py
```

### Environment Setup

#### Method 1: Using setup_env.sh (Recommended)
```bash
./setup_env.sh
```

#### Method 2: Using pip
```bash
pip install -r requirements.txt
```

#### Method 3: Using conda with environment.yml
```bash
conda env create -f environment.yml
conda activate coffee_dashboard
```

After starting the dashboard, open your browser and navigate to:
```
http://127.0.0.1:8050/
```

## Browser & Interface Notes

- For best performance, use Chrome, Firefox, or Edge
- The dashboard is responsive and works on both desktop and mobile devices
- All charts include interactive features:
  - Hover tooltips with detailed data
  - Zoom/pan capabilities
  - Click interactions for filtering
  - Download as PNG option

## Key Files
- `coffee_dashboard_revised.py`: Main dashboard application
- `run_final_dashboard_fixes.sh`: Dashboard launch script
- CSV data files: Source data for visualizations
- `requirements.txt` and `environment.yml`: Dependency specifications