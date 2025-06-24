#!/bin/bash

# Enhanced AWS Dashboard Startup Script
echo "🚀 Starting Enhanced AWS Dashboard with Cost Analysis, EC2 Real-time, and Lambda Logs..."

# Kill existing streamlit processes
echo "🔄 Stopping existing dashboard..."
pkill -f "streamlit.*realtime_ec2_dashboard"
pkill -f "streamlit.*enhanced_dashboard"
sleep 2

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  Virtual environment not found. Using system Python..."
fi

# Install additional required packages
echo "📦 Installing additional packages..."
pip install plotly streamlit-autorefresh

# Check AWS credentials
echo "🔍 Checking AWS credentials..."
if aws sts get-caller-identity > /dev/null 2>&1; then
    echo "✅ AWS credentials are valid"
else
    echo "❌ AWS credentials test failed. Please check your configuration."
    exit 1
fi

# Set region
export AWS_DEFAULT_REGION=ap-south-1

# Start the enhanced dashboard
echo ""
echo "🎯 Starting Enhanced AWS Dashboard..."
echo "📊 Features:"
echo "   • 💰 Cost Analysis - Monthly breakdown and optimization recommendations"
echo "   • 🖥️  EC2 Real-time - Live instance monitoring with CPU metrics"
echo "   • 📝 Lambda Logs - Real-time function logs and performance data"
echo "   • 📈 Overview - Infrastructure summary and insights"
echo ""
echo "🌐 Dashboard will be available at: http://13.232.173.188:8080"
echo "🔄 Auto-refresh enabled with dropdown selections"
echo "⏹️  Press Ctrl+C to stop"
echo ""

# Start with logging
streamlit run src/enhanced_dashboard.py \
    --server.port=8080 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    2>&1 | tee enhanced_dashboard.log
