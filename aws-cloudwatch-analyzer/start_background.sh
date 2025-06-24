#!/bin/bash

# Enhanced AWS Dashboard Background Startup Script
echo "🚀 Starting Enhanced AWS Dashboard in background..."

# Change to the correct directory
cd /home/ubuntu/aws-cloudwatch-analyzer

# Kill existing processes
echo "🔄 Stopping existing dashboard processes..."
pkill -f "streamlit.*realtime_ec2_dashboard" 2>/dev/null
pkill -f "streamlit.*enhanced_dashboard" 2>/dev/null
sleep 3

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Set AWS region
export AWS_DEFAULT_REGION=ap-south-1

# Check AWS credentials
echo "🔍 Checking AWS credentials..."
if aws sts get-caller-identity > /dev/null 2>&1; then
    echo "✅ AWS credentials are valid"
else
    echo "❌ AWS credentials test failed. Please check your configuration."
    exit 1
fi

# Install required packages if needed
pip install plotly streamlit-autorefresh > /dev/null 2>&1

# Create logs directory
mkdir -p logs

# Start the dashboard in background using nohup
echo "🎯 Starting Enhanced AWS Dashboard in background..."
echo "📊 Features: Cost Analysis | EC2 Real-time | Lambda Logs | Overview"
echo "🌐 Dashboard URL: http://13.232.173.188:8080"

nohup python -m streamlit run src/enhanced_dashboard.py \
    --server.port=8080 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --server.maxUploadSize=200 \
    > logs/enhanced_dashboard.log 2>&1 &

# Get the process ID
DASHBOARD_PID=$!
echo "📋 Dashboard started with PID: $DASHBOARD_PID"

# Save PID to file for easy management
echo $DASHBOARD_PID > logs/dashboard.pid

# Wait a moment and check if it's running
sleep 5

if ps -p $DASHBOARD_PID > /dev/null; then
    echo "✅ Dashboard is running successfully in background"
    echo "📊 Access your dashboard at: http://13.232.173.188:8080"
    echo "📝 Logs are being written to: logs/enhanced_dashboard.log"
    echo "🔄 To stop the dashboard, run: kill $DASHBOARD_PID"
    echo ""
    echo "🎛️ Dashboard Features:"
    echo "   • Cost Analysis with MCP integration"
    echo "   • EC2 Real-time monitoring"
    echo "   • Lambda function logs"
    echo "   • Infrastructure overview"
    echo "   • Auto-refresh capabilities"
else
    echo "❌ Dashboard failed to start. Check logs/enhanced_dashboard.log for details"
    exit 1
fi
