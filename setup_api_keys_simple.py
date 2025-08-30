#!/usr/bin/env python3
"""
Simplified API Key Setup Script
===============================

A more user-friendly version of the API key setup that handles validation
more gracefully and provides better guidance.

Usage:
    python3 setup_api_keys_simple.py
"""

import os
import sys
import getpass
from pathlib import Path

def check_project_structure():
    """Check if we're in the right directory"""
    if not Path("core/ai_manager.py").exists():
        print("❌ Please run this script from the AI Terminal project root directory")
        return False
    return True

def get_api_key_with_guidance(key_name):
    """Get API key with helpful guidance"""
    
    print(f"\n🔑 Setting up {key_name}:")
    
    # Provide specific guidance for each key type
    if key_name == 'groq_api_key':
        print("   📋 Groq API Key Setup:")
        print("   1. Go to: https://console.groq.com/keys")
        print("   2. Create a new API key")
        print("   3. Copy the key (starts with 'gsk_')")
        print("   4. Paste it below")
    elif key_name == 'gemini_api_key':
        print("   📋 Gemini API Key Setup:")
        print("   1. Go to: https://aistudio.google.com/app/apikey")
        print("   2. Create a new API key")
        print("   3. Copy the key (starts with 'AIza')")
        print("   4. Paste it below")
    
    while True:
        try:
            key_value = getpass.getpass(f"   Enter {key_name}: ").strip()
            
            if not key_value:
                print("   ⚠️  Key cannot be empty. Please try again.")
                continue
            
            # Basic validation
            if key_name == 'groq_api_key' and not key_value.startswith('gsk_'):
                print("   ⚠️  Groq API key should start with 'gsk_'")
                continue_anyway = input("   🤔 Continue anyway? (y/N): ").strip().lower()
                if continue_anyway in ['y', 'yes']:
                    return key_value
                continue
            elif key_name == 'gemini_api_key' and not key_value.startswith('AIza'):
                print("   ⚠️  Gemini API key should start with 'AIza'")
                continue_anyway = input("   🤔 Continue anyway? (y/N): ").strip().lower()
                if continue_anyway in ['y', 'yes']:
                    return key_value
                continue
            
            # Length check
            if len(key_value) < 20:
                print("   ⚠️  API key seems too short (should be at least 20 characters)")
                continue_anyway = input("   🤔 Continue anyway? (y/N): ").strip().lower()
                if continue_anyway in ['y', 'yes']:
                    return key_value
                continue
            
            return key_value
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Setup cancelled by user.")
            sys.exit(1)

def create_simple_config(keys):
    """Create a simple config file with the keys"""
    
    config_content = f"""[API_KEYS]
groq_api_key = {keys.get('groq_api_key', 'YOUR_GROQ_API_KEY_HERE')}
gemini_api_key = {keys.get('gemini_api_key', 'YOUR_GEMINI_API_KEY_HERE')}

[AI_MODELS]
default_model = auto
groq_model = llama3-8b-8192
gemini_model = gemini-1.5-flash

[SYSTEM]
max_tokens = 4096
temperature = 0.7
safety_mode = enabled
log_level = INFO

[WEB_INTERFACE]
host = localhost
port = 5000
debug = False
secret_key = CHANGE_THIS_SECRET_KEY
"""
    
    config_file = Path("config/ultra_config.ini")
    config_file.parent.mkdir(exist_ok=True)
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"   ✅ Configuration saved to {config_file}")

def main():
    """Main setup function"""
    
    print("🚀 AI Terminal - Simple API Key Setup")
    print("=" * 50)
    print("This script will help you configure your API keys quickly and easily.\n")
    
    # Check project structure
    if not check_project_structure():
        sys.exit(1)
    
    # Check if config already exists
    config_file = Path("config/ultra_config.ini")
    if config_file.exists():
        print("📋 Configuration file already exists.")
        response = input("❓ Do you want to update it? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("✅ Keeping existing configuration.")
            return
    
    # Collect API keys
    keys = {}
    
    # Groq API Key
    keys['groq_api_key'] = get_api_key_with_guidance('groq_api_key')
    
    # Gemini API Key
    keys['gemini_api_key'] = get_api_key_with_guidance('gemini_api_key')
    
    # Create configuration
    print("\n💾 Saving configuration...")
    create_simple_config(keys)
    
    print("\n🎉 Setup completed successfully!")
    print("✅ Your AI Terminal is now configured and ready to use.")
    
    print("\n🚀 Next Steps:")
    print("1. Start the AI Terminal:")
    print("   ./start_project.sh")
    print("")
    print("2. Access the web interface:")
    print("   http://localhost:5000")
    print("   Login: admin / admin123")
    print("")
    print("3. Use the terminal directly:")
    print("   python3 main.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)