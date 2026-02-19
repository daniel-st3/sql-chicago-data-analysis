#!/bin/bash
# Setup script for Chicago Data Analysis project

echo "============================================================"
echo "Chicago Data Analysis - Setup Script"
echo "============================================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "→ Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

echo ""
echo "→ Activating virtual environment..."
source venv/bin/activate

echo "→ Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

echo "✓ Dependencies installed successfully"
echo ""
echo "============================================================"
echo "Setup complete!"
echo "============================================================"
echo ""
echo "To run the analysis, use:"
echo "  python chicago_data_analysis.py"
echo ""
echo "To deactivate the virtual environment later, use:"
echo "  deactivate"
echo ""
