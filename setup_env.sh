#!/bin/bash

echo "Installing required packages one by one..."

# Try to install with pip first
pip install --upgrade pip
pip install dash --no-deps
pip install pandas
pip install numpy
pip install plotly

# Alternative installation with conda if available
if command -v conda &> /dev/null; then
    echo "Conda found, installing packages with conda as backup..."
    conda install -y dash pandas numpy plotly
fi

echo "Setup complete. Now you can run the dashboard with:"
echo "python coffee_dashboard.py"