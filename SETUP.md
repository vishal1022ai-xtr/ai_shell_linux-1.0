# 🚀 Setup Instructions

## 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/ai-terminal-web-interface.git
cd ai-terminal-web-interface
```

## 2. Configure API keys
```bash
# Edit config/ultra_config.ini
nano config/ultra_config.ini

# Add your real API keys:
# groq_api_key = YOUR_ACTUAL_GROQ_KEY
# gemini_api_key = YOUR_ACTUAL_GEMINI_KEY
```

## 3. Install dependencies
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip nmap

# Create virtual environment
cd web_interface
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_enhanced.txt
cd ..
```

## 4. Start the project
```bash
# Run startup script
./start_project.sh

# OR start manually
cd web_interface
python3 app_enhanced.py
```

## 5. Access the interface
- **URL**: http://localhost:5000
- **Login**: admin / admin123

## 🔐 API Key Setup

### Groq API Key
1. Go to [console.groq.com/keys](https://console.groq.com/keys)
2. Create a new API key
3. Copy the key and paste it in `config/ultra_config.ini`

### Gemini API Key
1. Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Copy the key and paste it in `config/ultra_config.ini`

## 🧪 Testing

```bash
# Run comprehensive tests
python3 test_full_project.py

# Run error checks
python3 error_check_test.py
```
