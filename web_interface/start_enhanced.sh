#!/bin/bash

# 🚀 Enhanced Unified AI Shell Web Interface - Startup Script
# Production-ready startup with comprehensive error handling and dependency management

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

print_success() {
    echo -e "${CYAN}🎉${NC} $1"
}

print_header() {
    echo -e "${PURPLE}$1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check system requirements
check_system_requirements() {
    print_header "🔍 Checking System Requirements..."
    
    # Check Python version
    if ! command_exists python3; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
    if [ -z "$PYTHON_VERSION" ]; then
        print_error "Could not determine Python version"
        exit 1
    fi
    
    # Check if Python version is sufficient (3.8+)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        print_error "Python 3.8 or higher is required. Current version: $PYTHON_VERSION"
        exit 1
    fi
    
    print_status "Python version: $PYTHON_VERSION"
    
    # Check for essential system packages
    print_info "Checking system dependencies..."
    
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        print_info "Detected Ubuntu/Debian system"
        
        # Check and install essential packages
        ESSENTIAL_PACKAGES=("python3-venv" "python3-pip" "python3-dev" "build-essential")
        MISSING_PACKAGES=()
        
        for package in "${ESSENTIAL_PACKAGES[@]}"; do
            if ! dpkg -l | grep -q "^ii  $package "; then
                MISSING_PACKAGES+=("$package")
            fi
        done
        
        if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
            print_warning "Installing missing system packages: ${MISSING_PACKAGES[*]}"
            sudo apt-get update
            sudo apt-get install -y "${MISSING_PACKAGES[@]}"
        fi
        
        # Check for audio dependencies
        if ! dpkg -l | grep -q "portaudio19-dev"; then
            print_warning "Installing portaudio19-dev (required for voice recognition)..."
            sudo apt-get install -y portaudio19-dev
        fi
        
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        print_info "Detected CentOS/RHEL system"
        
        if ! rpm -qa | grep -q "python3-devel"; then
            print_warning "Installing python3-devel..."
            sudo yum install -y python3-devel
        fi
        
        if ! rpm -qa | grep -q "portaudio-devel"; then
            print_warning "Installing portaudio-devel..."
            sudo yum install -y portaudio-devel
        fi
        
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        print_info "Detected Arch Linux system"
        
        if ! pacman -Q | grep -q "python-pip"; then
            print_warning "Installing python-pip..."
            sudo pacman -S python-pip
        fi
        
        if ! pacman -Q | grep -q "portaudio"; then
            print_warning "Installing portaudio..."
            sudo pacman -S portaudio
        fi
        
    else
        print_warning "Unknown package manager. Please install required dependencies manually."
    fi
    
    print_status "System requirements check completed"
}

# Function to setup virtual environment
setup_virtual_environment() {
    print_header "🐍 Setting up Virtual Environment..."
    
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
        print_status "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    print_info "Activating virtual environment..."
    source venv/bin/activate
    print_status "Virtual environment activated"
    
    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip
    print_status "Pip upgraded"
}

# Function to install Python dependencies
install_dependencies() {
    print_header "📦 Installing Python Dependencies..."
    
    # Check if requirements file exists
    if [ -f "requirements.txt" ]; then
        print_info "Installing dependencies from requirements.txt..."
        
        # Install core dependencies first
        print_info "Installing core dependencies..."
        pip install Flask Flask-SocketIO Flask-Login psutil
        
        # Install voice recognition dependencies
        print_info "Installing voice recognition dependencies..."
        pip install SpeechRecognition pydub PyAudio
        
        # Install remaining dependencies
        print_info "Installing remaining dependencies..."
        pip install -r requirements.txt
        
        print_status "All dependencies installed successfully"
    else
        print_warning "requirements.txt not found, installing core dependencies..."
        pip install Flask Flask-SocketIO Flask-Login SpeechRecognition pydub PyAudio psutil GPUtil
        print_status "Core dependencies installed"
    fi
    
    # Verify critical packages
    print_info "Verifying installation..."
    python3 -c "
import sys
required_packages = ['flask', 'flask_socketio', 'flask_login', 'psutil']
missing_packages = []

for package in required_packages:
    try:
        __import__(package)
        print(f'✓ {package} - OK')
    except ImportError:
        missing_packages.append(package)
        print(f'❌ {package} - MISSING')

if missing_packages:
    print(f'\\n❌ Missing packages: {missing_packages}')
    sys.exit(1)
else:
    print('\\n✅ All required packages are installed')
"
    
    if [ $? -ne 0 ]; then
        print_error "Some required packages are missing. Please check the installation."
        exit 1
    fi
}

# Function to create necessary directories
create_directories() {
    print_header "📁 Creating Necessary Directories..."
    
    DIRECTORIES=("logs" "uploads" "temp" "backups" "cache")
    
    for dir in "${DIRECTORIES[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "Created directory: $dir"
        else
            print_info "Directory already exists: $dir"
        fi
    done
    
    # Set proper permissions
    chmod 755 logs uploads temp backups cache
    print_status "Directory permissions set"
}

# Function to check AI Shell integration
check_ai_shell_integration() {
    print_header "🤖 Checking AI Shell Integration..."
    
    if [ -d "../core" ] && [ -d "../config" ]; then
        print_status "AI Shell components found"
        
        # Check if we can import AI Shell components
        python3 -c "
import sys
sys.path.append('/workspace')
try:
    from config.config_manager import ConfigManager
    from core.ai_manager import AIManager
    print('✅ AI Shell components are accessible')
except ImportError as e:
    print(f'⚠️  AI Shell components found but not accessible: {e}')
    sys.exit(1)
"
        
        if [ $? -eq 0 ]; then
            print_success "AI Shell integration verified"
        else
            print_warning "AI Shell integration has issues - some features may not work"
        fi
    else
        print_warning "AI Shell components not found in parent directory"
        print_warning "Some features may not work properly"
    fi
}

# Function to check network configuration
check_network_config() {
    print_header "🌐 Checking Network Configuration..."
    
    # Check if port 5000 is available
    if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port 5000 is already in use. Trying port 5001..."
        export FLASK_RUN_PORT=5001
        WEB_PORT=5001
    else
        export FLASK_RUN_PORT=5000
        WEB_PORT=5000
    fi
    
    # Get network information
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    EXTERNAL_IP=$(curl -s --max-time 5 https://api.ipify.org 2>/dev/null || echo "Unable to get")
    
    print_info "Network Configuration:"
    print_info "  • Local IP: $LOCAL_IP"
    print_info "  • External IP: $EXTERNAL_IP"
    print_info "  • Web Port: $WEB_PORT"
    
    # Check firewall status
    if command_exists ufw; then
        UFW_STATUS=$(sudo ufw status | grep -o "Status: .*")
        print_info "  • Firewall: $UFW_STATUS"
    fi
}

# Function to set environment variables
setup_environment() {
    print_header "⚙️  Setting Environment Variables..."
    
    export FLASK_ENV=development
    export FLASK_DEBUG=1
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    export PYTHONPATH="${PYTHONPATH}:/workspace"
    
    # Generate secret key if not exists
    if [ ! -f ".env" ]; then
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        echo "SECRET_KEY=$SECRET_KEY" > .env
        print_status "Generated new secret key"
    fi
    
    print_status "Environment variables configured"
}

# Function to display startup information
display_startup_info() {
    print_header "🎯 Enhanced Web Interface Configuration"
    echo ""
    echo "🚀 Features Enabled:"
    echo "  • Enhanced Security & Rate Limiting"
    echo "  • Comprehensive Error Handling"
    echo "  • Advanced PC Control Capabilities"
    echo "  • Voice Recognition & Control"
    echo "  • Real-time System Monitoring"
    echo "  • File Management & Editing"
    echo "  • AI Integration & Chat"
    echo ""
    echo "🔧 Technical Configuration:"
    echo "  • Host: 0.0.0.0 (accessible from any IP)"
    echo "  • Port: $WEB_PORT"
    echo "  • Environment: Development"
    echo "  • Debug Mode: Enabled"
    echo "  • Logging: Enhanced with file output"
    echo ""
    echo "🌐 Access Information:"
    echo "  • Local: http://localhost:$WEB_PORT"
    echo "  • Network: http://$LOCAL_IP:$WEB_PORT"
    echo "  • Login: admin / admin123"
    echo ""
    echo "🛡️  Security Features:"
    echo "  • Rate Limiting: 100 requests/minute"
    echo "  • Command Validation: Safe execution only"
    echo "  • File Access Control: Restricted directories"
    echo "  • User Authentication: Role-based access"
    echo "  • Session Management: Secure cookies"
    echo ""
}

# Function to start the web interface
start_web_interface() {
    print_header "🚀 Launching Enhanced Web Interface..."
    
    # Check if enhanced app exists
    if [ -f "app_enhanced.py" ]; then
        print_info "Starting enhanced web interface..."
        python3 app_enhanced.py
    else
        print_warning "Enhanced app not found, starting standard app..."
        python3 app.py
    fi
}

# Function to handle cleanup
cleanup() {
    print_info "Cleaning up..."
    # Add any cleanup tasks here
}

# Main execution
main() {
    print_header "🚀 Enhanced Unified AI Shell Web Interface - Startup"
    echo "================================================================"
    
    # Check if we're in the right directory
    if [ ! -f "app.py" ] && [ ! -f "app_enhanced.py" ]; then
        print_error "Please run this script from the web_interface directory"
        exit 1
    fi
    
    # Execute setup steps
    check_system_requirements
    setup_virtual_environment
    install_dependencies
    create_directories
    check_ai_shell_integration
    check_network_config
    setup_environment
    display_startup_info
    
    # Start the web interface
    start_web_interface
}

# Trap cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"