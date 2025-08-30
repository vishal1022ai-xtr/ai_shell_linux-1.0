#!/bin/bash

# 🚀 AI TERMINAL WITH WEB INTERFACE - STARTUP SCRIPT
# This script starts the complete AI Terminal project

echo "🚀 Starting AI Terminal with Web Interface..."
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "core/ai_manager.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected files: core/ai_manager.py"
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.8+ required, found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Check if logs directory exists
if [ ! -d "logs" ]; then
    echo "📁 Creating logs directory..."
    mkdir -p logs
fi

# Check if virtual environment exists
if [ ! -d "web_interface/venv" ]; then
    echo "🔧 Setting up virtual environment..."
    cd web_interface
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements_enhanced.txt
    cd ..
else
    echo "✅ Virtual environment found"
fi

# Test core components
echo "🧪 Testing core components..."
python3 test_full_project.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 All tests passed! Starting web interface..."
    echo ""
    
    # Start web interface
    cd web_interface
    echo "🌐 Starting web interface..."
    echo "📱 Access at: http://localhost:5000"
    echo "🔐 Login: admin / admin123"
    echo "⏹️  Press Ctrl+C to stop"
    echo ""
    
    # Activate virtual environment and start
    source venv/bin/activate
    python3 app_enhanced.py
    
else
    echo ""
    echo "❌ Some tests failed. Please fix the issues before starting."
    echo "   Check the test output above for details."
    exit 1
fi