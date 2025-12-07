#!/bin/bash

echo "================================================================================"
echo "UAE Legal Documents ETL Pipeline"
echo "================================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "Step 1: Checking dependencies..."
python3 -c "import pdfplumber, fitz, google.generativeai, dotenv" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Dependencies not installed. Installing now..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi
    echo "Dependencies installed successfully!"
else
    echo "Dependencies already installed."
fi

echo ""
echo "Step 2: Verifying setup..."
python3 test_setup.py
if [ $? -ne 0 ]; then
    echo ""
    echo "Setup verification failed. Please fix the issues above."
    exit 1
fi

echo ""
echo "Step 3: Running ETL pipeline..."
echo "This may take 5-15 minutes..."
echo ""
python3 main.py
if [ $? -ne 0 ]; then
    echo ""
    echo "Pipeline execution failed. Check the logs above."
    exit 1
fi

echo ""
echo "================================================================================"
echo "Pipeline completed successfully!"
echo "Output file: extracted_data.json"
echo "================================================================================"
echo ""
echo "Run 'python3 analyze_output.py' to analyze the results."
echo ""
