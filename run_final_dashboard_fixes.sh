#\!/bin/bash

# Check if Python is available
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "Python not found. Please install Python 3."
    exit 1
fi

# Run the coffee dashboard
echo "Starting the Coffee Dashboard with fixed trade flow visualization..."
"$PYTHON" coffee_dashboard_revised.py
