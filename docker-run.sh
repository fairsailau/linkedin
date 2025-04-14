#!/bin/bash

# LinkedIn Lead Scraper - Docker Deployment Script
# This script builds and runs the LinkedIn Lead Scraper application in a Docker container

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is required but not installed. Please install Docker and try again."
    exit 1
fi

# Build Docker image
echo "Building Docker image..."
docker build -t linkedin-lead-scraper .

# Run Docker container
echo "Starting LinkedIn Lead Scraper in Docker..."
docker run -p 8501:8501 linkedin-lead-scraper
