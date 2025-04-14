#!/bin/bash

# LinkedIn Lead Scraper - Deployment Script
# This script sets up and runs the LinkedIn Lead Scraper application

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install streamlit pandas selenium webdriver-manager beautifulsoup4 requests-html openpyxl plotly

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    echo "Creating data directory..."
    mkdir -p data
fi

# Run the application
echo "Starting LinkedIn Lead Scraper..."
streamlit run app.py

# Deactivate virtual environment on exit
deactivate
