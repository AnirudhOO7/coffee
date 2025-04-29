import sys
print(f"Python version: {sys.version}")

try:
    import dash
    print(f"Dash version: {dash.__version__}")
except ImportError:
    print("Dash not installed")

try:
    import pandas
    print(f"Pandas version: {pandas.__version__}")
except ImportError:
    print("Pandas not installed")

try:
    import numpy
    print(f"NumPy version: {numpy.__version__}")
except ImportError:
    print("NumPy not installed")

try:
    import plotly
    print(f"Plotly version: {plotly.__version__}")
except ImportError:
    print("Plotly not installed")

try:
    from dash import dcc
    print("dash.dcc is available")
except ImportError:
    print("dash.dcc not available")

try:
    import dash_core_components
    print("dash_core_components is available")
except ImportError:
    print("dash_core_components not available")