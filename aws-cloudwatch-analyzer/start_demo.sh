#!/bin/bash

# AWS CloudWatch Log Analyzer - Demo Mode Startup Script

echo "🎯 Starting AWS CloudWatch Log Analyzer - Demo Mode"
echo "=================================================="

# Navigate to project directory
cd /home/ubuntu/aws-cloudwatch-analyzer

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if Streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing dependencies..."
    pip install streamlit boto3 pandas plotly
fi

echo "🚀 Starting Streamlit application in demo mode..."
echo "📱 The application will be available at: http://localhost:8501"
echo "🔧 Use Ctrl+C to stop the application"
echo ""

# Start the demo application
streamlit run src/demo_mode.py --server.port=8501 --server.address=0.0.0.0
