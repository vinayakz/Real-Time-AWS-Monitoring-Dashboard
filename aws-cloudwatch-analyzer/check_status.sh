#!/bin/bash

# AWS CloudWatch Log Analyzer - Status Check Script

echo "🔍 AWS CloudWatch Log Analyzer - Status Check"
echo "=============================================="

# Check if application is running
if pgrep -f "streamlit" > /dev/null; then
    echo "✅ Application Status: RUNNING"
    
    # Get process details
    PID=$(pgrep -f "streamlit")
    echo "📋 Process ID: $PID"
    
    # Check HTTP response
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8501)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "🌐 HTTP Status: ✅ Accessible (HTTP $HTTP_CODE)"
        echo "🔗 URL: http://localhost:8501"
    else
        echo "🌐 HTTP Status: ❌ Not accessible (HTTP $HTTP_CODE)"
    fi
    
    # Check logs for errors
    if [ -f "streamlit.log" ]; then
        ERROR_COUNT=$(grep -i "error\|exception\|failed" streamlit.log | wc -l)
        if [ "$ERROR_COUNT" -gt 0 ]; then
            echo "⚠️  Errors in logs: $ERROR_COUNT (check streamlit.log)"
        else
            echo "📝 Logs: ✅ No errors detected"
        fi
    fi
    
else
    echo "❌ Application Status: NOT RUNNING"
    echo "🚀 To start: ./start_demo.sh or ./start_app.sh"
fi

echo ""

# Check AWS credentials
echo "🔐 AWS Credentials Check:"
if command -v aws &> /dev/null; then
    if aws sts get-caller-identity &> /dev/null; then
        echo "✅ AWS CLI: Configured and working"
        ACCOUNT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
        REGION=$(aws configure get region 2>/dev/null || echo "Not set")
        echo "📋 Account: $ACCOUNT"
        echo "🌍 Region: $REGION"
    else
        echo "⚠️  AWS CLI: Installed but not configured"
        echo "🔧 Run: aws configure"
    fi
else
    echo "❌ AWS CLI: Not installed"
fi

echo ""

# Check system resources
echo "💻 System Resources:"
MEMORY=$(free -h | awk '/^Mem:/ {print $3 "/" $2}')
DISK=$(df -h . | awk 'NR==2 {print $3 "/" $2 " (" $5 " used)"}')
echo "🧠 Memory: $MEMORY"
echo "💾 Disk: $DISK"

echo ""

# Check dependencies
echo "📦 Dependencies:"
cd /home/ubuntu/aws-cloudwatch-analyzer
if [ -d "venv" ]; then
    echo "✅ Virtual Environment: Present"
    source venv/bin/activate
    if python3 -c "import streamlit, boto3, pandas, plotly" 2>/dev/null; then
        echo "✅ Python Packages: All required packages installed"
    else
        echo "❌ Python Packages: Missing dependencies"
        echo "🔧 Run: pip install -r requirements/requirements.txt"
    fi
else
    echo "❌ Virtual Environment: Not found"
    echo "🔧 Run: python3 -m venv venv"
fi

echo ""
echo "=============================================="
if pgrep -f "streamlit" > /dev/null && [ "$HTTP_CODE" = "200" ]; then
    echo "🎉 Overall Status: ✅ HEALTHY AND RUNNING"
    echo "🌐 Access your application at: http://localhost:8501"
else
    echo "⚠️  Overall Status: ❌ NEEDS ATTENTION"
    echo "🔧 Check the issues above and restart if needed"
fi
echo "=============================================="
