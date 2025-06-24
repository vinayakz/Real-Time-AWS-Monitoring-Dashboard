#!/bin/bash

# AWS CloudWatch Log Analyzer - Full Application Startup Script

echo "🎯 Starting AWS CloudWatch Log Analyzer - Full Mode"
echo "=================================================="

# Navigate to project directory
cd /home/ubuntu/aws-cloudwatch-analyzer

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check AWS credentials
echo "🔐 Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "⚠️  AWS credentials not configured or invalid."
    echo "📋 Please configure AWS credentials using one of these methods:"
    echo "   1. aws configure"
    echo "   2. Set environment variables:"
    echo "      export AWS_ACCESS_KEY_ID=your_access_key"
    echo "      export AWS_SECRET_ACCESS_KEY=your_secret_key"
    echo "      export AWS_DEFAULT_REGION=us-east-1"
    echo "   3. Use IAM roles (if running on EC2)"
    echo ""
    echo "🎯 Starting in demo mode instead..."
    streamlit run src/demo_mode.py --server.port=8501 --server.address=0.0.0.0
else
    echo "✅ AWS credentials configured successfully"
    echo "🚀 Starting full application with AWS integration..."
    echo "📱 The application will be available at: http://localhost:8501"
    echo "🔧 Use Ctrl+C to stop the application"
    echo ""
    
    # Start the full application
    streamlit run src/main.py --server.port=8501 --server.address=0.0.0.0
fi
