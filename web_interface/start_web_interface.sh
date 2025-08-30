#!/bin/bash

# 🚀 Unified AI Shell Web Interface - Startup Script
# This script sets up and launches the web-based control center

set -e  # Exit on any error

echo "🚀 Starting Unified AI Shell Web Interface..."
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    print_error "Please run this script from the web_interface directory"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
if [ -z "$PYTHON_VERSION" ]; then
    print_error "Python 3 is not installed or not accessible"
    exit 1
fi

print_status "Python version: $PYTHON_VERSION"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_status "Virtual environment activated"

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip

# Install system dependencies (if needed)
print_info "Checking system dependencies..."
if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    print_info "Detected Ubuntu/Debian system"
    if ! dpkg -l | grep -q "portaudio19-dev"; then
        print_warning "Installing portaudio19-dev (required for voice recognition)..."
        sudo apt-get update
        sudo apt-get install -y portaudio19-dev python3-dev
    fi
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    print_info "Detected CentOS/RHEL system"
    if ! rpm -qa | grep -q "portaudio-devel"; then
        print_warning "Installing portaudio-devel (required for voice recognition)..."
        sudo yum install -y portaudio-devel python3-dev
    fi
fi

# Install Python dependencies
print_info "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_status "Dependencies installed successfully"
else
    print_warning "requirements.txt not found, installing core dependencies..."
    pip install Flask Flask-SocketIO Flask-Login SpeechRecognition pydub psutil
    print_status "Core dependencies installed"
fi

# Check if all required packages are installed
print_info "Verifying installation..."
python3 -c "
import sys
required_packages = ['flask', 'flask_socketio', 'flask_login', 'speech_recognition', 'psutil']
missing_packages = []

for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    print(f'Missing packages: {missing_packages}')
    sys.exit(1)
else:
    print('All required packages are installed')
"

if [ $? -ne 0 ]; then
    print_error "Some required packages are missing. Please check the installation."
    exit 1
fi

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p logs
mkdir -p uploads
mkdir -p temp
print_status "Directories created"

# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=1
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if port 5000 is available
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Port 5000 is already in use. Trying port 5001..."
    export FLASK_RUN_PORT=5001
    WEB_PORT=5001
else
    export FLASK_RUN_PORT=5000
    WEB_PORT=5000
fi

# Display startup information
echo ""
echo "🎯 Web Interface Configuration:"
echo "   • Host: 0.0.0.0 (accessible from any IP)"
echo "   • Port: $WEB_PORT"
echo "   • Environment: Development"
echo "   • Debug Mode: Enabled"
echo ""

# Check if we can access the AI Shell
print_info "Checking AI Shell integration..."
if [ -d "../core" ] && [ -d "../config" ]; then
    print_status "AI Shell components found"
else
    print_warning "AI Shell components not found in parent directory"
    print_warning "Some features may not work properly"
fi

# Display access information
echo ""
echo "🌐 Access Information:"
echo "   • Local: http://localhost:$WEB_PORT"
echo "   • Network: http://$(hostname -I | awk '{print $1}'):$WEB_PORT"
echo "   • Login: admin / admin123"
echo ""

# Start the web interface
print_info "Launching web interface..."
echo "🚀 Starting Flask application..."
echo "================================================"

# Run the Flask application
python3 app.py

# If we reach here, the application has stopped
echo ""
print_info "Web interface has stopped"
print_info "To restart, run: ./start_web_interface.sh"