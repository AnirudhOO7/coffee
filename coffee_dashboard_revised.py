import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Load and prepare data
production_data = pd.read_csv('Coffee_production_modified.csv')
consumption_data = pd.read_csv('Coffee_domestic_consumption_modified.csv')
import_data = pd.read_csv('Coffee_import.csv')
export_data = pd.read_csv('Coffee_export.csv')
trade_flow_data = pd.read_csv('synthetic_coffee_trade_flows.csv')

# Initialize the Dash app
app = dash.Dash(__name__, 
                suppress_callback_exceptions=True,
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}])
server = app.server

# Coffee theme colors
COFFEE_COLORS = {
    'dark_brown': '#4A2C2A',
    'medium_brown': '#6B4226',
    'light_brown': '#967259',
    'tan': '#B99C6B',
    'cream': '#F5EBDC',
    'background': '#FAF7F2',
    'text': '#33211F'
}

# Create a color scale from coffee colors
COFFEE_COLORSCALE = [
    COFFEE_COLORS['cream'], 
    COFFEE_COLORS['tan'], 
    COFFEE_COLORS['light_brown'], 
    COFFEE_COLORS['medium_brown'], 
    COFFEE_COLORS['dark_brown']
]

# Preprocess data
years = [str(year) for year in range(1990, 2020)]

# Clean export data - replace invalid values
export_data = export_data.replace(-2147483648, np.nan)

# Extract coffee types
coffee_types = production_data['Coffee type'].unique()

# Helper functions
def get_top_countries(df, year_col, n=10):
    """Get top n countries based on values for a specific year column"""
    top_countries = df.sort_values(by=year_col, ascending=False).head(n)['Country'].tolist()
    return top_countries

def get_annual_totals(df, coffee_type=None):
    """Calculate annual totals for each year, optionally filtered by coffee type"""
    if coffee_type:
        filtered_df = df[df['Coffee type'].str.contains(coffee_type)]
    else:
        filtered_df = df
        
    annual_totals = {year: filtered_df[year].sum() for year in years}
    return pd.DataFrame({'Year': years, 'Total': list(annual_totals.values())})

def get_coffee_type_totals(df, year):
    """Get production/consumption totals by coffee type for a specific year"""
    print("Calculating coffee type totals...")
    
    # Initialize a dictionary to track totals by type
    type_totals = {
        'Arabica': 0,
        'Robusta': 0,
        'Arabica/Robusta': 0  # Changed from 'Other' to 'Arabica/Robusta'
    }
    
    # Process each row
    for _, row in df.iterrows():
        coffee_type = row['Coffee type']
        value = row[year]
        
        if pd.isna(value):
            continue
        
        # Print some rows for debugging
        if _ < 5:
            print(f"Processing row {_}: {coffee_type}, value: {value}")
            
        if 'Arabica' in coffee_type and 'Robusta' not in coffee_type:
            type_totals['Arabica'] += value
        elif 'Robusta' in coffee_type and 'Arabica' not in coffee_type:
            type_totals['Robusta'] += value
        elif 'Arabica' in coffee_type and 'Robusta' in coffee_type:
            # Now put it in Arabica/Robusta category instead of splitting
            type_totals['Arabica/Robusta'] += value
        else:
            # Fallback - should not happen with this dataset
            print(f"Warning: Unknown coffee type: {coffee_type}")
    
    # Print the totals for debugging
    print(f"Type totals: Arabica={type_totals['Arabica']:,.0f}, Robusta={type_totals['Robusta']:,.0f}, Arabica/Robusta={type_totals['Arabica/Robusta']:,.0f}")
    
    # Convert to the expected DataFrame format with fixed column names
    type_data = [
        {'Coffee Type': 'Arabica', 'Value': type_totals['Arabica']},
        {'Coffee Type': 'Robusta', 'Value': type_totals['Robusta']},
        {'Coffee Type': 'Arabica/Robusta', 'Value': type_totals['Arabica/Robusta']}
    ]
    
    # Create and return the DataFrame, ensuring all records are included
    result_df = pd.DataFrame(type_data)
    print(f"Coffee type DataFrame has {len(result_df)} rows")
    return result_df

def get_production_consumption_by_year():
    """Calculate total production and consumption by year"""
    prod_by_year = {year: production_data[year].sum() for year in years}
    cons_by_year = {year: consumption_data[year].sum() for year in years}
    
    result_data = []
    for year in years:
        result_data.append({
            'Year': year, 
            'Production': prod_by_year[year], 
            'Consumption': cons_by_year[year]
        })
    
    return pd.DataFrame(result_data)

# App layout
app.layout = html.Div([
    # Header
    html.Div([
        html.Img(src='https://cdn-icons-png.flaticon.com/512/4396/4396449.png', 
                 style={'height': '60px', 'margin-right': '15px'}),
        html.H1('Coffee Dashboard', style={'display': 'inline-block', 'vertical-align': 'middle', 'color': COFFEE_COLORS['dark_brown']})
    ], style={'text-align': 'center', 'margin-bottom': '20px', 'margin-top': '20px'}),
    
    # Navigation
    html.Div([
        dcc.Tabs(id='tabs', value='production', children=[
            dcc.Tab(label='Production', value='production'),
            dcc.Tab(label='Consumption', value='consumption'),
            dcc.Tab(label='Import', value='import'),
            dcc.Tab(label='Export', value='export'),
            dcc.Tab(label='Trade Flow', value='trade-flow'),
        ], style={'font-weight': 'bold'})
    ]),
    
    # Content
    html.Div(id='tabs-content')
], style={'max-width': '1200px', 'margin': '0 auto', 'padding': '20px', 'background-color': COFFEE_COLORS['background']})

# Callbacks for tab content
@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value')
)
def render_content(tab):
    if tab == 'production':
        return render_production_tab()
    elif tab == 'consumption':
        return render_consumption_tab()
    elif tab == 'import':
        return render_import_tab()
    elif tab == 'export':
        return render_export_tab()
    elif tab == 'trade-flow':
        return render_trade_flow_tab()
    return html.Div([html.H3('Tab content not found')])

# Production Tab
def render_production_tab():
    return html.Div([
        # Year slider for filtering
        html.Div([
            html.H3('Select Year:', style={'margin-bottom': '10px', 'color': COFFEE_COLORS['medium_brown']}),
            dcc.Slider(
                id='production-year-slider',
                min=1990,
                max=2019,
                step=1,
                marks={year: str(year) for year in range(1990, 2020, 5)},
                value=2019,
                tooltip={"placement": "bottom", "always_visible": True}
            ),
        ], style={'margin-bottom': '30px'}),
        
        # First row: Treemap and Countries List - using flexbox for guaranteed side-by-side placement
        html.Div(style={
            'display': 'flex', 
            'flexDirection': 'row', 
            'flexWrap': 'nowrap',
            'marginBottom': '20px'
        }, children=[
            # Left side: Treemap
            html.Div(style={
                'width': '60%', 
                'minWidth': '500px',
                'marginRight': '15px'
            }, children=[
                dcc.Graph(id='production-treemap', style={'height': '450px'})
            ]),
            
            # Right side: Countries List
            html.Div(style={
                'width': '40%',
                'minWidth': '300px',
                'backgroundColor': 'white', 
                'padding': '15px', 
                'borderRadius': '5px', 
                'boxShadow': '0px 0px 10px rgba(0,0,0,0.1)'
            }, children=[
                html.H3('Top Producing Countries', style={'color': COFFEE_COLORS['medium_brown'], 'textAlign': 'center'}),
                html.Div(id='production-countries-list', style={'height': '400px', 'overflowY': 'auto'})
            ])
        ]),
        
        # Second row: Radial Chart
        html.Div([
            dcc.Graph(id='production-radial')
        ], className='row'),
        
        # Second row: Production Trend Line Chart
        html.Div([
            dcc.Graph(id='production-trend-line')
        ], className='row'),
        
        # Third row: Coffee Types Bar Chart and Production vs Consumption
        html.Div([
            html.Div([
                dcc.Graph(id='coffee-type-bar')
            ], className='six columns'),
            html.Div([
                dcc.Graph(id='prod-vs-cons-by-year')
            ], className='six columns'),
        ], className='row'),
        
        # Last row: Bar Chart with Dot Indicators
        html.Div([
            dcc.Graph(id='prod-vs-cons-by-country')
        ], className='row'),
    ])

# Consumption Tab
def render_consumption_tab():
    return html.Div([
        # Year slider for filtering
        html.Div([
            html.H3('Select Year:', style={'margin-bottom': '10px', 'color': COFFEE_COLORS['medium_brown']}),
            dcc.Slider(
                id='consumption-year-slider',
                min=1990,
                max=2019,
                step=1,
                marks={year: str(year) for year in range(1990, 2020, 5)},
                value=2019,
                tooltip={"placement": "bottom", "always_visible": True}
            ),
        ], style={'margin-bottom': '30px'}),
        
        # First row: Treemap and Countries List - using flexbox like production page
        html.Div(style={
            'display': 'flex', 
            'flexDirection': 'row', 
            'flexWrap': 'nowrap',
            'marginBottom': '20px'
        }, children=[
            # Left side: Treemap
            html.Div(style={
                'width': '60%', 
                'minWidth': '500px',
                'marginRight': '15px'
            }, children=[
                dcc.Graph(id='consumption-treemap', style={'height': '450px'})
            ]),
            
            # Right side: Countries List
            html.Div(style={
                'width': '40%',
                'minWidth': '300px',
                'backgroundColor': 'white', 
                'padding': '15px', 
                'borderRadius': '5px', 
                'boxShadow': '0px 0px 10px rgba(0,0,0,0.1)'
            }, children=[
                html.H3('Top Consuming Countries', style={'color': COFFEE_COLORS['medium_brown'], 'textAlign': 'center'}),
                html.Div(id='consumption-countries-list', style={'height': '400px', 'overflowY': 'auto'})
            ])
        ]),
        
        # Second row: Radial Chart
        html.Div([
            dcc.Graph(id='consumption-radial')
        ], className='row'),
        
        # Third row: Consumption Trend Line Chart
        html.Div([
            dcc.Graph(id='consumption-trend-line')
        ], className='row'),
        
        # Fourth row: Coffee Type Bar Chart
        html.Div([
            dcc.Graph(id='consumption-coffee-type-bar')
        ], className='row'),
        
        # Fifth row: Consumption Types - All Group (matching production page)
        html.Div([
            dcc.Graph(id='consumption-types-all')
        ], className='row'),
        
        # Last row: Bar Chart with Dot Indicators - with slider
        html.Div([
            dcc.Graph(id='cons-vs-prod-by-country')
        ], className='row'),
    ])

# Import Tab
def render_import_tab():
    return html.Div([
        # Year slider for filtering
        html.Div([
            html.H3('Select Year:', style={'margin-bottom': '10px', 'color': COFFEE_COLORS['medium_brown']}),
            dcc.Slider(
                id='import-year-slider',
                min=1990,
                max=2019,
                step=1,
                marks={year: str(year) for year in range(1990, 2020, 5)},
                value=2019,
                tooltip={"placement": "bottom", "always_visible": True}
            ),
        ], style={'margin-bottom': '30px'}),
        
        # First row: Treemap and Countries List - using flexbox like other tabs
        html.Div(style={
            'display': 'flex', 
            'flexDirection': 'row', 
            'flexWrap': 'nowrap',
            'marginBottom': '20px'
        }, children=[
            # Left side: Treemap
            html.Div(style={
                'width': '60%', 
                'minWidth': '500px',
                'marginRight': '15px'
            }, children=[
                dcc.Graph(id='import-treemap', style={'height': '450px'})
            ]),
            
            # Right side: Countries List
            html.Div(style={
                'width': '40%',
                'minWidth': '300px',
                'backgroundColor': 'white', 
                'padding': '15px', 
                'borderRadius': '5px', 
                'boxShadow': '0px 0px 10px rgba(0,0,0,0.1)'
            }, children=[
                html.H3('Top Importing Countries', style={'color': COFFEE_COLORS['medium_brown'], 'textAlign': 'center'}),
                html.Div(id='import-countries-list', style={'height': '400px', 'overflowY': 'auto'})
            ])
        ]),
        
        # Second row: Radial Chart
        html.Div([
            dcc.Graph(id='import-radial')
        ], className='row'),
        
        # Third row: Import Trend Line Chart
        html.Div([
            dcc.Graph(id='import-trend-line')
        ], className='row'),
    ])

# Export Tab
def render_export_tab():
    return html.Div([
        # Year slider for filtering
        html.Div([
            html.H3('Select Year:', style={'margin-bottom': '10px', 'color': COFFEE_COLORS['medium_brown']}),
            dcc.Slider(
                id='export-year-slider',
                min=1990,
                max=2019,
                step=1,
                marks={year: str(year) for year in range(1990, 2020, 5)},
                value=2019,
                tooltip={"placement": "bottom", "always_visible": True}
            ),
        ], style={'margin-bottom': '30px'}),
        
        # First row: Treemap and Countries List - using flexbox like other tabs
        html.Div(style={
            'display': 'flex', 
            'flexDirection': 'row', 
            'flexWrap': 'nowrap',
            'marginBottom': '20px'
        }, children=[
            # Left side: Treemap
            html.Div(style={
                'width': '60%', 
                'minWidth': '500px',
                'marginRight': '15px'
            }, children=[
                dcc.Graph(id='export-treemap', style={'height': '450px'})
            ]),
            
            # Right side: Countries List
            html.Div(style={
                'width': '40%',
                'minWidth': '300px',
                'backgroundColor': 'white', 
                'padding': '15px', 
                'borderRadius': '5px', 
                'boxShadow': '0px 0px 10px rgba(0,0,0,0.1)'
            }, children=[
                html.H3('Top Exporting Countries', style={'color': COFFEE_COLORS['medium_brown'], 'textAlign': 'center'}),
                html.Div(id='export-countries-list', style={'height': '400px', 'overflowY': 'auto'})
            ])
        ]),
        
        # Second row: Radial Chart
        html.Div([
            dcc.Graph(id='export-radial')
        ], className='row'),
        
        # Third row: Export Trend Line Chart
        html.Div([
            dcc.Graph(id='export-trend-line')
        ], className='row'),
    ])

# Trade Flow Tab
def render_trade_flow_tab():
    # Get all countries from export and import data
    all_exporting_countries = sorted(export_data['Country'].unique().tolist())
    all_importing_countries = sorted(import_data['Country'].unique().tolist())
    
    return html.Div([
        html.Div([
            html.H3('Coffee Trade Flow Analysis', style={'color': COFFEE_COLORS['medium_brown']}),
            
            # Year selector
            html.P('Select a year to visualize global coffee trade flows:'),
            dcc.Slider(
                id='trade-flow-year-slider',
                min=1990,
                max=2019,
                step=1,
                marks={year: str(year) for year in range(1990, 2020, 5)},
                value=2019,
                tooltip={"placement": "bottom", "always_visible": True}
            ),
            html.Div(id='trade-flow-year-display', style={'margin-top': '20px', 'font-weight': 'bold', 'color': COFFEE_COLORS['medium_brown']}),
            
            # Country filters
            html.Div([
                html.Div([
                    html.Label('Filter by Exporting Country (optional):'),
                    dcc.Dropdown(
                        id='exporting-country-filter',
                        options=[{'label': country, 'value': country} for country in all_exporting_countries],
                        value=None,
                        placeholder="Select a country (optional)",
                        style={'width': '100%'}
                    )
                ], style={'width': '48%', 'display': 'inline-block', 'margin-right': '2%'}),
                
                html.Div([
                    html.Label('Filter by Importing Country (optional):'),
                    dcc.Dropdown(
                        id='importing-country-filter',
                        options=[{'label': country, 'value': country} for country in all_importing_countries],
                        value=None,
                        placeholder="Select a country (optional)",
                        style={'width': '100%'}
                    )
                ], style={'width': '48%', 'display': 'inline-block'})
            ], style={'margin-top': '20px', 'margin-bottom': '20px'})
            
        ], style={'margin-bottom': '30px'}),
        
        html.Div([
            dcc.Graph(id='trade-flow-sankey')
        ]),
        
        html.Div([
            html.H4('Top Exporting Countries', style={'color': COFFEE_COLORS['medium_brown']}),
            html.Div(id='top-exporters-table')
        ], style={'margin-top': '30px'}),
        
        html.Div([
            html.H4('Top Importing Countries', style={'color': COFFEE_COLORS['medium_brown']}),
            html.Div(id='top-importers-table')
        ], style={'margin-top': '30px'})
    ])

# Production Tab Callbacks
@app.callback(
    [Output('production-treemap', 'figure'),
     Output('production-countries-list', 'children'),
     Output('production-radial', 'figure'),
     Output('production-trend-line', 'figure'),
     Output('coffee-type-bar', 'figure'),
     Output('prod-vs-cons-by-year', 'figure'),
     Output('prod-vs-cons-by-country', 'figure')],
    [Input('production-year-slider', 'value')]
)
def update_production_charts(selected_year):
    year_str = str(selected_year)
    
    # 1. Treemap Chart - just by country, not by coffee type
    tree_map_data = production_data[['Country', year_str]].copy()
    tree_map_data = tree_map_data[tree_map_data[year_str] > 0]
    tree_map_data.columns = ['Country', 'Value']
    
    # Verify data values are correct by printing some totals
    print(f"Total production for {year_str}: {tree_map_data['Value'].sum():,.0f}")
    
    treemap_fig = px.treemap(
        tree_map_data, 
        path=['Country'], 
        values='Value',
        color='Value',
        color_continuous_scale=COFFEE_COLORSCALE,
        title=f'Coffee Production by Country ({year_str})'
    )
    treemap_fig.update_layout(
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background']
    )
    
    # 2. Countries List in descending order
    countries_data = tree_map_data.groupby('Country')['Value'].sum().sort_values(ascending=False)
    
    # Create a formatted table of countries
    countries_rows = []
    for i, (country, value) in enumerate(countries_data.items()):
        countries_rows.append(
            html.Tr([
                html.Td(f"{i+1}.", style={'width': '10%', 'textAlign': 'right', 'paddingRight': '10px'}),
                html.Td(country, style={'width': '60%'}),
                html.Td(f"{value:,.0f}", style={'width': '30%', 'textAlign': 'right'})
            ], style={'backgroundColor': COFFEE_COLORS['cream'] if i % 2 == 0 else 'white'})
        )
    
    countries_table = html.Table(
        [html.Thead(
            html.Tr([
                html.Th("Rank", style={'width': '10%', 'textAlign': 'right'}),
                html.Th("Country", style={'width': '60%'}),
                html.Th("Production", style={'width': '30%', 'textAlign': 'right'})
            ], style={'backgroundColor': COFFEE_COLORS['medium_brown'], 'color': 'white'})
        )] + 
        [html.Tbody(countries_rows)],
        style={'width': '100%', 'borderCollapse': 'collapse'}
    )
    
    # 2. Radial Chart for top 10 producers
    top_producers = get_top_countries(production_data, year_str, 10)
    top_production_data = production_data[production_data['Country'].isin(top_producers)]
    radial_data = top_production_data[['Country', year_str]].copy()
    radial_data.columns = ['Country', 'Value']
    
    # Add "Others" category
    other_countries = production_data[~production_data['Country'].isin(top_producers)]
    other_value = other_countries[year_str].sum()
    radial_data = pd.concat([radial_data, pd.DataFrame([{'Country': 'Others', 'Value': other_value}])])
    
    radial_fig = px.pie(
        radial_data,
        names='Country', 
        values='Value',
        hole=0.4,
        title=f'Top 10 Coffee Producers ({year_str})',
        color_discrete_sequence=COFFEE_COLORSCALE
    )
    radial_fig.update_layout(
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background']
    )
    
    # 3. Production Trend Line Chart (across all years with trend line)
    total_production = get_annual_totals(production_data)
    
    trend_fig = go.Figure()
    trend_fig.add_trace(
        go.Scatter(
            x=total_production['Year'],
            y=total_production['Total'],
            mode='lines+markers',
            name='Total Production',
            line=dict(color=COFFEE_COLORS['medium_brown'], width=2),
            marker=dict(size=8, color=COFFEE_COLORS['dark_brown'])
        )
    )
    
    # Add trend line
    z = np.polyfit(range(len(years)), total_production['Total'], 1)
    p = np.poly1d(z)
    trend_fig.add_trace(
        go.Scatter(
            x=total_production['Year'],
            y=p(range(len(years))),
            mode='lines',
            name='Trend',
            line=dict(color=COFFEE_COLORS['tan'], width=2, dash='dash')
        )
    )
    
    trend_fig.update_layout(
        title='Production Across Years (1990-2019)',
        xaxis_title='Year',
        yaxis_title='Production Volume',
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background'],
        hovermode='x unified'
    )
    
    # 4. Coffee Types Bar Chart (actual production volumes for the selected year)
    coffee_type_data = get_coffee_type_totals(production_data, year_str)
    
    # Convert values to K format
    coffee_type_data['Value_K'] = coffee_type_data['Value'] / 1000
    
    # Create bar chart
    type_fig = go.Figure()
    
    # Add bars
    type_fig.add_trace(go.Bar(
        x=coffee_type_data['Coffee Type'],
        y=coffee_type_data['Value_K'],
        marker_color=[COFFEE_COLORS['medium_brown'], COFFEE_COLORS['light_brown'], COFFEE_COLORS['tan']],
        text=coffee_type_data['Value_K'].apply(lambda x: f"{x:,.2f}K"),
        textposition='outside'
    ))
    
    # Format to match style from production.png
    type_fig.update_layout(
        title=f'Production by Coffee Type ({year_str})',
        font=dict(size=14),
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background'],
        margin=dict(t=50, b=50, l=50, r=50),
        showlegend=False,
        xaxis=dict(title=None),
        yaxis=dict(title="Production Volume (thousands)")
    )
    
    # 5. Production types bar chart showing totals by type
    # Based on the production.png reference image
    
    # Calculate total production by type
    total_arabica = 0
    total_robusta = 0
    total_mixed = 0  # For Arabica/Robusta combined
    
    # Process each country row
    for _, row in production_data.iterrows():
        coffee_type = row['Coffee type']
        
        # Calculate total production for all years for this country
        country_total = 0
        for year in years:
            if pd.notna(row[year]):
                country_total += row[year]
        
        # Assign to appropriate type
        if coffee_type == 'Arabica':
            total_arabica += country_total
        elif coffee_type == 'Robusta':
            total_robusta += country_total
        elif 'Arabica/Robusta' in coffee_type or 'Robusta/Arabica' in coffee_type:
            total_mixed += country_total
    
    # Print totals for verification
    print(f"Total Arabica: {total_arabica:,.2f}K")
    print(f"Total Robusta: {total_robusta:,.2f}K")
    print(f"Total Arabica/Robusta: {total_mixed:,.2f}K")
    
    # Create data for the chart
    prod_type_data = pd.DataFrame([
        {'Coffee Type': 'Arabica\nProduction', 'Value': total_arabica / 1000},  # Convert to K units
        {'Coffee Type': 'Robusta\nProduction', 'Value': total_robusta / 1000},
        {'Coffee Type': 'Other\nProduction', 'Value': total_mixed / 1000}
    ])
    
    # Create bar chart matching production.png
    pvc_fig = go.Figure()
    
    # Add bars
    pvc_fig.add_trace(go.Bar(
        x=prod_type_data['Coffee Type'],
        y=prod_type_data['Value'],
        marker_color=[COFFEE_COLORS['medium_brown'], COFFEE_COLORS['light_brown'], COFFEE_COLORS['tan']],
        text=prod_type_data['Value'].apply(lambda x: f"{x:,.2f}K"),
        textposition='outside'
    ))
    
    # Format to match production.png
    pvc_fig.update_layout(
        title='Production Types - All Group',
        font=dict(size=14),
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background'],
        margin=dict(t=50, b=50, l=50, r=50),
        yaxis=dict(
            title=None,
            showticklabels=False,
            showgrid=False
        ),
        xaxis=dict(
            title=None
        ),
        showlegend=False
    )
    
    # 6. Production vs Consumption by Country for selected year - using direct data from datasets
    print("Creating Production vs Consumption by Country chart...")
    
    # First get all countries that have both production and consumption data
    prod_countries = set(production_data['Country'])
    cons_countries = set(consumption_data['Country'])
    common_countries = list(prod_countries.intersection(cons_countries))
    
    # Prepare data for these countries
    pvc_country_data = []
    for country in common_countries:
        # Extract exact values from datasets
        prod_value = production_data.loc[production_data['Country'] == country, year_str].values[0]
        cons_value = consumption_data.loc[consumption_data['Country'] == country, year_str].values[0]
        
        # Only include if both values are positive
        if prod_value > 0 and cons_value > 0:
            pvc_country_data.append({
                'Country': country,
                'Production': prod_value,
                'Consumption': cons_value
            })
    
    # Sort by production value (descending)
    pvc_country_df = pd.DataFrame(pvc_country_data)
    pvc_country_df = pvc_country_df.sort_values('Production', ascending=False).head(30)
    
    print(f"Found {len(pvc_country_df)} countries with both production and consumption data")
    print(f"Top 5 countries: {pvc_country_df.head(5)['Country'].tolist()}")
    
    # Create figure with scrollable x-axis
    pvc_country_fig = go.Figure()
    pvc_country_fig.add_trace(
        go.Bar(
            x=pvc_country_df['Country'],
            y=pvc_country_df['Production'],
            name='Production',
            marker_color='#8b572a'  # Medium coffee brown
        )
    )
    
    pvc_country_fig.add_trace(
        go.Scatter(
            x=pvc_country_df['Country'],
            y=pvc_country_df['Consumption'],
            mode='markers',
            name='Consumption',
            marker=dict(
                size=14,
                color='#5D1A00',  # Darker brown
                symbol='circle'
            )
        )
    )
    
    # Make the x-axis scrollable by limiting the initial view to 10 countries
    visible_countries = 10
    
    pvc_country_fig.update_layout(
        title=f'Production vs Consumption by Country ({year_str}) - Scroll to see more',
        xaxis_title='Country',
        yaxis_title='Volume',
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background'],
        xaxis=dict(
            range=[0, visible_countries - 0.5],
            rangeslider=dict(visible=True),
            type='category'
        ),
        margin=dict(b=100),  # Add space at bottom for the slider
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    
    return treemap_fig, countries_table, radial_fig, trend_fig, type_fig, pvc_fig, pvc_country_fig

# Consumption Tab Callbacks
@app.callback(
    [Output('consumption-treemap', 'figure'),
     Output('consumption-countries-list', 'children'),
     Output('consumption-radial', 'figure'),
     Output('consumption-trend-line', 'figure'),
     Output('consumption-coffee-type-bar', 'figure'),
     Output('consumption-types-all', 'figure'),
     Output('cons-vs-prod-by-country', 'figure')],
    [Input('consumption-year-slider', 'value')]
)
def update_consumption_charts(selected_year):
    year_str = str(selected_year)
    
    # 1. Treemap for consumption - similar to production, just by country not by type
    tree_map_data = consumption_data[['Country', year_str]].copy()
    tree_map_data = tree_map_data[tree_map_data[year_str] > 0]
    tree_map_data.columns = ['Country', 'Value']
    
    # Print data totals for verification
    print(f"Total consumption for {year_str}: {tree_map_data['Value'].sum():,.0f}")
    
    treemap_fig = px.treemap(
        tree_map_data, 
        path=['Country'], 
        values='Value',
        color='Value',
        color_continuous_scale=COFFEE_COLORSCALE,
        title=f'Coffee Consumption by Country ({year_str})'
    )
    treemap_fig.update_layout(
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background']
    )
    
    # 2. Countries List in descending order - same format as production page
    countries_data = tree_map_data.sort_values('Value', ascending=False)
    
    # Create a formatted table of countries
    countries_rows = []
    for i, row in enumerate(countries_data.itertuples()):
        countries_rows.append(
            html.Tr([
                html.Td(f"{i+1}.", style={'width': '10%', 'textAlign': 'right', 'paddingRight': '10px'}),
                html.Td(row.Country, style={'width': '60%'}),
                html.Td(f"{row.Value:,.0f}", style={'width': '30%', 'textAlign': 'right'})
            ], style={'backgroundColor': COFFEE_COLORS['cream'] if i % 2 == 0 else 'white'})
        )
    
    countries_table = html.Table(
        [html.Thead(
            html.Tr([
                html.Th("Rank", style={'width': '10%', 'textAlign': 'right'}),
                html.Th("Country", style={'width': '60%'}),
                html.Th("Consumption", style={'width': '30%', 'textAlign': 'right'})
            ], style={'backgroundColor': COFFEE_COLORS['medium_brown'], 'color': 'white'})
        )] + 
        [html.Tbody(countries_rows)],
        style={'width': '100%', 'borderCollapse': 'collapse'}
    )
    
    # 2. Radial chart for top 10 consumers
    top_consumers = get_top_countries(consumption_data, year_str, 10)
    top_consumption_data = consumption_data[consumption_data['Country'].isin(top_consumers)]
    radial_data = top_consumption_data[['Country', year_str]].copy()
    radial_data.columns = ['Country', 'Value']
    
    # Add "Others" category
    other_countries = consumption_data[~consumption_data['Country'].isin(top_consumers)]
    other_value = other_countries[year_str].sum()
    radial_data = pd.concat([radial_data, pd.DataFrame([{'Country': 'Others', 'Value': other_value}])])
    
    radial_fig = px.pie(
        radial_data,
        names='Country', 
        values='Value',
        hole=0.4,
        title=f'Top 10 Coffee Consumers ({year_str})',
        color_discrete_sequence=COFFEE_COLORSCALE
    )
    radial_fig.update_layout(
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background']
    )
    
    # 3. Consumption trend line chart
    total_consumption = get_annual_totals(consumption_data)
    
    trend_fig = go.Figure()
    trend_fig.add_trace(
        go.Scatter(
            x=total_consumption['Year'],
            y=total_consumption['Total'],
            mode='lines+markers',
            name='Total Consumption',
            line=dict(color=COFFEE_COLORS['medium_brown'], width=2),
            marker=dict(size=8, color=COFFEE_COLORS['dark_brown'])
        )
    )
    
    # Add trend line
    z = np.polyfit(range(len(years)), total_consumption['Total'], 1)
    p = np.poly1d(z)
    trend_fig.add_trace(
        go.Scatter(
            x=total_consumption['Year'],
            y=p(range(len(years))),
            mode='lines',
            name='Trend',
            line=dict(color=COFFEE_COLORS['tan'], width=2, dash='dash')
        )
    )
    
    trend_fig.update_layout(
        title='Consumption Across Years (1990-2019)',
        xaxis_title='Year',
        yaxis_title='Consumption Volume',
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background'],
        hovermode='x unified'
    )
    
    # 4. Consumption Growth Bar Chart - Annual growth rates from previous year
    growth_data = []
    
    for i in range(1, len(years)):
        prev_year = years[i-1]
        curr_year = years[i]
        
        total_prev = consumption_data[prev_year].sum()
        total_curr = consumption_data[curr_year].sum()
        
        if total_prev > 0:
            growth_pct = (total_curr - total_prev) / total_prev * 100
            growth_data.append({'Year': curr_year, 'Growth': growth_pct})
    
    growth_df = pd.DataFrame(growth_data)
    
    growth_fig = px.bar(
        growth_df,
        x='Year',
        y='Growth',
        title='Annual Consumption Growth Rate (%)',
        text_auto='.1f',
        color='Growth',
        color_continuous_scale=COFFEE_COLORSCALE
    )
    
    # Highlight the selected year
    if str(selected_year) in growth_df['Year'].values:
        growth_fig.add_shape(
            type="rect",
            x0=str(selected_year - 0.4),
            x1=str(selected_year + 0.4),
            y0=0,
            y1=growth_df.loc[growth_df['Year'] == str(selected_year), 'Growth'].values[0] * 1.1 
                if growth_df.loc[growth_df['Year'] == str(selected_year), 'Growth'].values[0] > 0 
                else growth_df.loc[growth_df['Year'] == str(selected_year), 'Growth'].values[0] * 0.9,
            line=dict(width=0),
            fillcolor=COFFEE_COLORS['cream'],
            opacity=0.3
        )
    
    growth_fig.update_layout(
        xaxis_title='Year',
        yaxis_title='Growth Rate (%)',
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background']
    )
    
    # 5. Consumption vs Production by Year
    pvc_yearly = get_production_consumption_by_year()
    
    pvc_fig = go.Figure()
    pvc_fig.add_trace(
        go.Bar(
            x=pvc_yearly['Year'],
            y=pvc_yearly['Consumption'],
            name='Consumption',
            marker_color=COFFEE_COLORS['medium_brown']
        )
    )
    pvc_fig.add_trace(
        go.Scatter(
            x=pvc_yearly['Year'],
            y=pvc_yearly['Production'],
            mode='markers',
            name='Production',
            marker=dict(
                size=12,
                color=COFFEE_COLORS['dark_brown'],
                symbol='circle'
            )
        )
    )
    
    # Highlight the selected year
    pvc_fig.add_shape(
        type="rect",
        x0=str(int(year_str) - 0.4),
        x1=str(int(year_str) + 0.4),
        y0=0,
        y1=pvc_yearly.loc[pvc_yearly['Year'] == year_str, 'Consumption'].values[0] * 1.1,
        line=dict(width=0),
        fillcolor=COFFEE_COLORS['cream'],
        opacity=0.3
    )
    
    pvc_fig.update_layout(
        title='Consumption vs Production by Year (1990-2019)',
        xaxis_title='Year',
        yaxis_title='Volume',
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background'],
        hovermode='x unified'
    )
    
    # 6. Consumption vs Production by Country - with slider like production page
    print("Creating Consumption vs Production by Country chart...")
    
    # First get all countries that have both production and consumption data
    cons_countries = set(consumption_data['Country'])
    prod_countries = set(production_data['Country'])
    common_countries = list(cons_countries.intersection(prod_countries))
    
    # Prepare data for these countries
    cons_vs_prod_data = []
    for country in common_countries:
        # Extract exact values from datasets
        cons_value = consumption_data.loc[consumption_data['Country'] == country, year_str].values[0]
        prod_value = production_data.loc[production_data['Country'] == country, year_str].values[0]
        
        # Only include if both values are positive
        if cons_value > 0 and prod_value > 0:
            cons_vs_prod_data.append({
                'Country': country,
                'Consumption': cons_value,
                'Production': prod_value
            })
    
    # Sort by consumption value (descending)
    cons_vs_prod_df = pd.DataFrame(cons_vs_prod_data)
    cons_vs_prod_df = cons_vs_prod_df.sort_values('Consumption', ascending=False).head(30)
    
    print(f"Found {len(cons_vs_prod_df)} countries with both consumption and production data")
    print(f"Top 5 countries: {cons_vs_prod_df.head(5)['Country'].tolist()}")
    
    # Create figure with scrollable x-axis
    cons_vs_prod_fig = go.Figure()
    cons_vs_prod_fig.add_trace(
        go.Bar(
            x=cons_vs_prod_df['Country'],
            y=cons_vs_prod_df['Consumption'],
            name='Consumption',
            marker_color='#8b572a'  # Medium coffee brown
        )
    )
    
    cons_vs_prod_fig.add_trace(
        go.Scatter(
            x=cons_vs_prod_df['Country'],
            y=cons_vs_prod_df['Production'],
            mode='markers',
            name='Production',
            marker=dict(
                size=14,
                color='#5D1A00',  # Darker brown
                symbol='circle'
            )
        )
    )
    
    # Make the x-axis scrollable by limiting the initial view to 10 countries
    visible_countries = 10
    
    # Find a better y-axis range to make lower values more visible
    max_value = max(
        cons_vs_prod_df['Consumption'].max(),
        cons_vs_prod_df['Production'].max()
    )
    
    # Use log scale or a reduced linear scale to better show the range of values
    use_log_scale = True  # Set to False for linear scale with adjusted range
    
    if use_log_scale:
        # Log scale makes small values more visible
        cons_vs_prod_fig.update_layout(
            title=f'Consumption vs Production by Country ({year_str}) - Scroll to see more',
            xaxis_title='Country',
            yaxis_title='Volume (log scale)',
            font_color=COFFEE_COLORS['text'],
            paper_bgcolor=COFFEE_COLORS['background'],
            plot_bgcolor=COFFEE_COLORS['background'],
            xaxis=dict(
                range=[0, visible_countries - 0.5],
                rangeslider=dict(visible=True),
                type='category'
            ),
            yaxis=dict(
                type='log',  # Log scale makes small values more visible
                title='Volume (log scale)'
            ),
            margin=dict(b=100),  # Add space at bottom for the slider
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            )
        )
    else:
        # Alternative: Linear scale with adjusted range
        # Find 90th percentile value to use as max y-axis value
        # This will "cut off" the top 10% of values but make the lower 90% more visible
        p90_value = np.percentile(
            cons_vs_prod_df[['Consumption', 'Production']].values.flatten(),
            90
        )
        
        cons_vs_prod_fig.update_layout(
            title=f'Consumption vs Production by Country ({year_str}) - Scroll to see more',
            xaxis_title='Country',
            yaxis_title='Volume',
            font_color=COFFEE_COLORS['text'],
            paper_bgcolor=COFFEE_COLORS['background'],
            plot_bgcolor=COFFEE_COLORS['background'],
            xaxis=dict(
                range=[0, visible_countries - 0.5],
                rangeslider=dict(visible=True),
                type='category'
            ),
            yaxis=dict(
                range=[0, p90_value * 1.1],  # Show up to 110% of the 90th percentile value
                title='Volume'
            ),
            margin=dict(b=100),  # Add space at bottom for the slider
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            )
        )
    
    # 4. Coffee Types Bar Chart - in K format like production page
    coffee_type_data = get_coffee_type_totals(consumption_data, year_str)
    
    # Convert values to K format
    coffee_type_data['Value_K'] = coffee_type_data['Value'] / 1000
    
    # Create bar chart
    coffee_type_fig = go.Figure()
    
    # Add bars
    coffee_type_fig.add_trace(go.Bar(
        x=coffee_type_data['Coffee Type'],
        y=coffee_type_data['Value_K'],
        marker_color=[COFFEE_COLORS['medium_brown'], COFFEE_COLORS['light_brown'], COFFEE_COLORS['tan']],
        text=coffee_type_data['Value_K'].apply(lambda x: f"{x:,.2f}K"),
        textposition='outside'
    ))
    
    # Format to match style from production page
    coffee_type_fig.update_layout(
        title=f'Consumption by Coffee Type ({year_str})',
        font=dict(size=14),
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background'],
        margin=dict(t=50, b=50, l=50, r=50),
        showlegend=False,
        xaxis=dict(title=None),
        yaxis=dict(title="Consumption Volume (thousands)")
    )
    
    # 5. Consumption Types - All Group
    # Calculate total consumption by type across all years
    total_arabica = 0
    total_robusta = 0
    total_mixed = 0  # For Arabica/Robusta combined
    
    # Process each country row
    for _, row in consumption_data.iterrows():
        coffee_type = row['Coffee type']
        
        # Calculate total consumption for all years for this country
        country_total = 0
        for year in years:
            if pd.notna(row[year]):
                country_total += row[year]
        
        # Assign to appropriate type
        if coffee_type == 'Arabica':
            total_arabica += country_total
        elif coffee_type == 'Robusta':
            total_robusta += country_total
        elif 'Arabica/Robusta' in coffee_type or 'Robusta/Arabica' in coffee_type:
            total_mixed += country_total
    
    # Print totals for verification
    print(f"Total Consumption - Arabica: {total_arabica:,.2f}K")
    print(f"Total Consumption - Robusta: {total_robusta:,.2f}K")
    print(f"Total Consumption - Arabica/Robusta: {total_mixed:,.2f}K")
    
    # Create data for the chart
    cons_type_data = pd.DataFrame([
        {'Coffee Type': 'Arabica\nConsumption', 'Value': total_arabica / 1000},  # Convert to K units
        {'Coffee Type': 'Robusta\nConsumption', 'Value': total_robusta / 1000},
        {'Coffee Type': 'Other\nConsumption', 'Value': total_mixed / 1000}
    ])
    
    # Create bar chart matching production page style
    cons_types_fig = go.Figure()
    
    # Add bars
    cons_types_fig.add_trace(go.Bar(
        x=cons_type_data['Coffee Type'],
        y=cons_type_data['Value'],
        marker_color=[COFFEE_COLORS['medium_brown'], COFFEE_COLORS['light_brown'], COFFEE_COLORS['tan']],
        text=cons_type_data['Value'].apply(lambda x: f"{x:,.2f}K"),
        textposition='outside'
    ))
    
    # Format to match production.png
    cons_types_fig.update_layout(
        title='Consumption Types - All Group',
        font=dict(size=14),
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background'],
        margin=dict(t=50, b=50, l=50, r=50),
        yaxis=dict(
            title=None,
            showticklabels=False,
            showgrid=False
        ),
        xaxis=dict(
            title=None
        ),
        showlegend=False
    )
    
    return treemap_fig, countries_table, radial_fig, trend_fig, coffee_type_fig, cons_types_fig, cons_vs_prod_fig

# Import Tab Callbacks
@app.callback(
    [Output('import-treemap', 'figure'),
     Output('import-countries-list', 'children'),
     Output('import-radial', 'figure'),
     Output('import-trend-line', 'figure')],
    [Input('import-year-slider', 'value')]
)
def update_import_charts(selected_year):
    year_str = str(selected_year)
    
    # 1. Treemap for imports - just by country like the production page
    tree_map_data = import_data[['Country', year_str]].copy()
    tree_map_data = tree_map_data[tree_map_data[year_str] > 0]
    tree_map_data.columns = ['Country', 'Value']
    
    # Print data totals for verification
    print(f"Total import for {year_str}: {tree_map_data['Value'].sum():,.0f}")
    
    treemap_fig = px.treemap(
        tree_map_data, 
        path=['Country'], 
        values='Value',
        color='Value',
        color_continuous_scale=COFFEE_COLORSCALE,
        title=f'Coffee Import by Country ({year_str})'
    )
    treemap_fig.update_layout(
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background']
    )
    
    # 2. Countries List in descending order - same format as other pages
    countries_data = tree_map_data.sort_values('Value', ascending=False)
    
    # Create a formatted table of countries
    countries_rows = []
    for i, row in enumerate(countries_data.itertuples()):
        countries_rows.append(
            html.Tr([
                html.Td(f"{i+1}.", style={'width': '10%', 'textAlign': 'right', 'paddingRight': '10px'}),
                html.Td(row.Country, style={'width': '60%'}),
                html.Td(f"{row.Value:,.0f}", style={'width': '30%', 'textAlign': 'right'})
            ], style={'backgroundColor': COFFEE_COLORS['cream'] if i % 2 == 0 else 'white'})
        )
    
    countries_table = html.Table(
        [html.Thead(
            html.Tr([
                html.Th("Rank", style={'width': '10%', 'textAlign': 'right'}),
                html.Th("Country", style={'width': '60%'}),
                html.Th("Import", style={'width': '30%', 'textAlign': 'right'})
            ], style={'backgroundColor': COFFEE_COLORS['medium_brown'], 'color': 'white'})
        )] + 
        [html.Tbody(countries_rows)],
        style={'width': '100%', 'borderCollapse': 'collapse'}
    )
    
    # 3. Radial chart for top 10 importers
    top_importers = get_top_countries(import_data, year_str, 10)
    top_import_data = import_data[import_data['Country'].isin(top_importers)]
    radial_data = top_import_data[['Country', year_str]].copy()
    radial_data.columns = ['Country', 'Value']
    
    # Add "Others" category
    other_countries = import_data[~import_data['Country'].isin(top_importers)]
    other_value = other_countries[year_str].sum()
    radial_data = pd.concat([radial_data, pd.DataFrame([{'Country': 'Others', 'Value': other_value}])])
    
    radial_fig = px.pie(
        radial_data,
        names='Country', 
        values='Value',
        hole=0.4,
        title=f'Top 10 Coffee Importers ({year_str})',
        color_discrete_sequence=COFFEE_COLORSCALE
    )
    radial_fig.update_layout(
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background']
    )
    
    # 4. Import trend line chart
    annual_totals = {year: import_data[year].sum() for year in years}
    trend_data = pd.DataFrame({'Year': years, 'Total': list(annual_totals.values())})
    
    trend_fig = go.Figure()
    trend_fig.add_trace(
        go.Scatter(
            x=trend_data['Year'],
            y=trend_data['Total'],
            mode='lines+markers',
            name='Total Imports',
            line=dict(color=COFFEE_COLORS['medium_brown'], width=2),
            marker=dict(size=8, color=COFFEE_COLORS['dark_brown'])
        )
    )
    
    # Add trend line
    z = np.polyfit(range(len(years)), trend_data['Total'], 1)
    p = np.poly1d(z)
    trend_fig.add_trace(
        go.Scatter(
            x=trend_data['Year'],
            y=p(range(len(years))),
            mode='lines',
            name='Trend',
            line=dict(color=COFFEE_COLORS['tan'], width=2, dash='dash')
        )
    )
    
    trend_fig.update_layout(
        title='Import Volumes Across Years (1990-2019)',
        xaxis_title='Year',
        yaxis_title='Import Volume',
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background'],
        hovermode='x unified'
    )
    
    return treemap_fig, countries_table, radial_fig, trend_fig

# Export Tab Callbacks
@app.callback(
    [Output('export-treemap', 'figure'),
     Output('export-countries-list', 'children'),
     Output('export-radial', 'figure'),
     Output('export-trend-line', 'figure')],
    [Input('export-year-slider', 'value')]
)
def update_export_charts(selected_year):
    year_str = str(selected_year)
    
    # Handle missing values in export data
    export_data_clean = export_data.replace(-2147483648, np.nan)
    
    # 1. Treemap for exports by country
    export_latest = export_data_clean[['Country', year_str]].copy()
    export_latest = export_latest[export_latest[year_str].notna()]
    export_latest.columns = ['Country', 'Value']
    
    # Print data totals for verification
    print(f"Total export for {year_str}: {export_latest['Value'].sum():,.0f}")
    
    # Create treemap
    treemap_fig = px.treemap(
        export_latest, 
        path=['Country'], 
        values='Value',
        color='Value',
        color_continuous_scale=COFFEE_COLORSCALE,
        title=f'Coffee Export by Country ({year_str})'
    )
    treemap_fig.update_layout(
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background']
    )
    
    # 2. Countries List in descending order - same format as other pages
    countries_data = export_latest.sort_values('Value', ascending=False)
    
    # Create a formatted table of countries
    countries_rows = []
    for i, row in enumerate(countries_data.itertuples()):
        if pd.notna(row.Value):
            countries_rows.append(
                html.Tr([
                    html.Td(f"{i+1}.", style={'width': '10%', 'textAlign': 'right', 'paddingRight': '10px'}),
                    html.Td(row.Country, style={'width': '60%'}),
                    html.Td(f"{row.Value:,.0f}", style={'width': '30%', 'textAlign': 'right'})
                ], style={'backgroundColor': COFFEE_COLORS['cream'] if i % 2 == 0 else 'white'})
            )
    
    countries_table = html.Table(
        [html.Thead(
            html.Tr([
                html.Th("Rank", style={'width': '10%', 'textAlign': 'right'}),
                html.Th("Country", style={'width': '60%'}),
                html.Th("Export", style={'width': '30%', 'textAlign': 'right'})
            ], style={'backgroundColor': COFFEE_COLORS['medium_brown'], 'color': 'white'})
        )] + 
        [html.Tbody(countries_rows)],
        style={'width': '100%', 'borderCollapse': 'collapse'}
    )
    
    # 3. Radial chart for top 10 exporters
    top_exporters = get_top_countries(export_data_clean, year_str, 10)
    top_export_data = export_data_clean[export_data_clean['Country'].isin(top_exporters)]
    radial_data = top_export_data[['Country', year_str]].copy()
    radial_data.columns = ['Country', 'Value']
    
    # Remove NaN values
    radial_data = radial_data.dropna()
    
    # Add "Others" category
    other_countries = export_data_clean[~export_data_clean['Country'].isin(top_exporters)]
    other_value = other_countries[year_str].sum()
    radial_data = pd.concat([radial_data, pd.DataFrame([{'Country': 'Others', 'Value': other_value}])])
    
    radial_fig = px.pie(
        radial_data,
        names='Country', 
        values='Value',
        hole=0.4,
        title=f'Top 10 Coffee Exporters ({year_str})',
        color_discrete_sequence=COFFEE_COLORSCALE
    )
    radial_fig.update_layout(
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background']
    )
    
    # 4. Export trend line chart
    annual_totals = {year: export_data_clean[year].sum() for year in years}
    trend_data = pd.DataFrame({'Year': years, 'Total': list(annual_totals.values())})
    
    trend_fig = go.Figure()
    trend_fig.add_trace(
        go.Scatter(
            x=trend_data['Year'],
            y=trend_data['Total'],
            mode='lines+markers',
            name='Total Exports',
            line=dict(color=COFFEE_COLORS['medium_brown'], width=2),
            marker=dict(size=8, color=COFFEE_COLORS['dark_brown'])
        )
    )
    
    # Add trend line
    z = np.polyfit(range(len(years)), trend_data['Total'].fillna(0), 1)
    p = np.poly1d(z)
    trend_fig.add_trace(
        go.Scatter(
            x=trend_data['Year'],
            y=p(range(len(years))),
            mode='lines',
            name='Trend',
            line=dict(color=COFFEE_COLORS['tan'], width=2, dash='dash')
        )
    )
    
    trend_fig.update_layout(
        title='Export Volumes Across Years (1990-2019)',
        xaxis_title='Year',
        yaxis_title='Export Volume',
        font_color=COFFEE_COLORS['text'],
        paper_bgcolor=COFFEE_COLORS['background'],
        plot_bgcolor=COFFEE_COLORS['background'],
        hovermode='x unified'
    )
    
    return treemap_fig, countries_table, radial_fig, trend_fig

# Trade Flow Tab Callbacks
@app.callback(
    [Output('trade-flow-sankey', 'figure'),
     Output('trade-flow-year-display', 'children'),
     Output('top-exporters-table', 'children'),
     Output('top-importers-table', 'children')],
    [Input('trade-flow-year-slider', 'value'),
     Input('exporting-country-filter', 'value'),
     Input('importing-country-filter', 'value')]
)
def update_trade_flow(selected_year, selected_exporter, selected_importer):
    # Make sure selected_year is properly converted to numeric for filtering
    year_int = int(selected_year) if isinstance(selected_year, str) else selected_year
    
    # Use the trade flow data from CSV file which contains connections between countries
    # NOTE: We're working with the complete dataset to ensure all trade flows are captured
    print(f"Total trade flow records in dataset: {len(trade_flow_data)}")
    
    # Filter by year
    # Year in the CSV appears to be an integer, so compare with integer value
    filtered_data = trade_flow_data[trade_flow_data['Year'] == year_int].copy()
    print(f"Trade flow data for year {year_int}: {len(filtered_data)} records")
    
    # Apply exporter filter if provided
    if selected_exporter:
        filtered_data = filtered_data[filtered_data['Exporter'] == selected_exporter]
        print(f"After filtering by exporter {selected_exporter}: {len(filtered_data)} records")
    
    # Apply importer filter if provided
    if selected_importer:
        filtered_data = filtered_data[filtered_data['Importer'] == selected_importer]
        print(f"After filtering by importer {selected_importer}: {len(filtered_data)} records")
    
    # If we have trade flow data after filtering
    if len(filtered_data) > 0:
        # Get total values for each exporter and importer
        all_exporters = filtered_data.groupby('Exporter')['Quantity'].sum().sort_values(ascending=False)
        all_importers = filtered_data.groupby('Importer')['Quantity'].sum().sort_values(ascending=False)
        
        # Limit number of nodes in Sankey diagram for better visualization
        if selected_exporter or selected_importer:
            # If filtering is applied, show all related countries
            top_filtered_data = filtered_data.copy()
            exporter_names = filtered_data['Exporter'].unique().tolist()
            importer_names = filtered_data['Importer'].unique().tolist()
        else:
            # Otherwise limit to top countries
            MAX_NODES = 15  # Show top 15 countries on each side
            exporter_names = all_exporters.head(MAX_NODES).index.tolist()
            importer_names = all_importers.head(MAX_NODES).index.tolist()
            
            # Filter data for only top exporters and importers
            top_filtered_data = filtered_data[
                (filtered_data['Exporter'].isin(exporter_names)) & 
                (filtered_data['Importer'].isin(importer_names))
            ]
        
        print(f"Creating sankey with {len(exporter_names)} exporters and {len(importer_names)} importers")
        print(f"Top exporters: {exporter_names[:5]}")
        print(f"Top importers: {importer_names[:5]}")
            
        # Create unique nodes list for the Sankey diagram
        # Need to create a strict separation between sources (exporters) and targets (importers)
        all_nodes = []
        
        # Add all exporters first (these will be source nodes)
        for country in exporter_names:
            if country not in all_nodes:
                all_nodes.append(country)
                
        # Add all importers (target nodes)
        for country in importer_names:
            if country not in all_nodes:
                all_nodes.append(country)
        
        # Create node indices dictionary
        node_indices = {node: i for i, node in enumerate(all_nodes)}
        
        # Create link data for sankey diagram
        link_data = []
        for _, row in top_filtered_data.iterrows():
            exporter = row['Exporter']
            importer = row['Importer']
            quantity = row['Quantity']
            
            # Only add link if both countries are in our nodes list
            if exporter in node_indices and importer in node_indices:
                # Get source and target indices
                source_idx = node_indices[exporter]
                target_idx = node_indices[importer]
                
                link_data.append({
                    'source': source_idx,
                    'target': target_idx,
                    'value': quantity,
                    'label': f"{exporter} → {importer}"
                })
        
        print(f"Created {len(link_data)} links for Sankey diagram")
        
        # Create source, target and value lists for Sankey
        sources = [link['source'] for link in link_data]
        targets = [link['target'] for link in link_data]
        values = [link['value'] for link in link_data]
        
        # Create Sankey diagram
        sankey_fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_nodes,
                color=[COFFEE_COLORS['light_brown'] if i < len(exporter_names) 
                       else COFFEE_COLORS['tan'] for i in range(len(all_nodes))]
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values
            )
        )])
        
        # Create title with filter information
        title = f"Coffee Trade Flows in {selected_year}"
        if selected_exporter:
            title += f" - Exporter: {selected_exporter}"
        if selected_importer:
            title += f" - Importer: {selected_importer}"
            
        sankey_fig.update_layout(
            title_text=title,
            font_color=COFFEE_COLORS['text'],
            paper_bgcolor=COFFEE_COLORS['background'],
            plot_bgcolor=COFFEE_COLORS['background'],
            font_size=10,
            height=600
        )
        
        # Get top exporters and importers for the tables
        top_exporters = all_exporters.head(15)
        top_importers = all_importers.head(15)
    else:
        # Create an empty Sankey diagram with a message if no flows match the filters
        sankey_fig = go.Figure()
        
        # Show text message when no data found
        message = f"No Coffee Trade Flows Found for Year: {selected_year}"
        if selected_exporter:
            message += f", Exporter: {selected_exporter}"
        if selected_importer:
            message += f", Importer: {selected_importer}"
            
        sankey_fig.add_annotation(
            text=message,
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(color=COFFEE_COLORS['dark_brown'], size=18)
        )
        
        sankey_fig.update_layout(
            title_text="No matching trade flows found",
            font_color=COFFEE_COLORS['text'],
            paper_bgcolor=COFFEE_COLORS['background'],
            plot_bgcolor=COFFEE_COLORS['background'],
            height=600
        )
        
        # Empty tables when no data
        top_exporters = pd.Series()
        top_importers = pd.Series()
    
    # Create tables for top exporters and importers
    exporter_table = html.Table([
        html.Thead(
            html.Tr([html.Th("Exporter"), html.Th("Quantity")])
        ),
        html.Tbody([
            html.Tr([
                html.Td(country),
                html.Td(f"{int(quantity):,}")
            ]) for country, quantity in top_exporters.items()
        ])
    ], style={'width': '100%', 'border-collapse': 'collapse'})
    
    importer_table = html.Table([
        html.Thead(
            html.Tr([html.Th("Importer"), html.Th("Quantity")])
        ),
        html.Tbody([
            html.Tr([
                html.Td(country),
                html.Td(f"{int(quantity):,}")
            ]) for country, quantity in top_importers.items()
        ])
    ], style={'width': '100%', 'border-collapse': 'collapse'})
    
    # Update the year display
    filter_text = ""
    if selected_exporter:
        filter_text += f" | Exporting Country: {selected_exporter}"
    if selected_importer:
        filter_text += f" | Importing Country: {selected_importer}"
        
    year_display = f"Showing coffee trade flows for {selected_year}{filter_text}"
    
    return sankey_fig, year_display, exporter_table, importer_table

# Add CSS for styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Coffee Dashboard</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: "Helvetica Neue", Arial, sans-serif;
                background-color: ''' + COFFEE_COLORS['background'] + ''';
                color: ''' + COFFEE_COLORS['text'] + ''';
            }
            .dash-tab {
                border-radius: 5px 5px 0 0;
                border-color: #ddd;
                border-bottom: none;
                background-color: ''' + COFFEE_COLORS['cream'] + ''';
            }
            .dash-tab--selected {
                border-top: 3px solid ''' + COFFEE_COLORS['medium_brown'] + ''';
                background-color: white;
            }
            h1, h2, h3, h4 {
                color: ''' + COFFEE_COLORS['medium_brown'] + ''';
            }
            table {
                border-collapse: collapse;
                width: 100%;
            }
            th, td {
                text-align: left;
                padding: 8px;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: ''' + COFFEE_COLORS['medium_brown'] + ''';
                color: white;
            }
            tr:nth-child(even) {
                background-color: ''' + COFFEE_COLORS['cream'] + ''';
            }
            .row:after {
                content: "";
                display: table;
                clear: both;
            }
            .six.columns {
                width: 48%;
                float: left;
                margin-right: 2%;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Run the app
if __name__ == '__main__':
    try:
        app.run(debug=True)  # For newer versions of Dash
    except AttributeError:
        app.run_server(debug=True)  # For older versions of Dash