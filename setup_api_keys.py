#!/usr/bin/env python3
"""
AI Terminal API Key Setup Script
================================

Simple script to setup API keys for the AI Terminal project.
This script will guide you through setting up your API keys securely.

Usage:
    python3 setup_api_keys.py

Author: AI Terminal Project
License: MIT
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    
    print("✅ Python version:", sys.version.split()[0])
    
    # Check if we're in the right directory
    if not Path("core/ai_manager.py").exists():
        print("❌ Please run this script from the AI Terminal project root directory")
        return False
    
    print("✅ Project structure verified")
    
    # Check if secure key manager exists
    if not Path("config/secure_key_manager.py").exists():
        print("❌ Secure key manager not found. Please ensure all files are present.")
        return False
    
    print("✅ Secure key manager found")
    
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing required packages...")
    
    packages = [
        "keyring",
        "cryptography"
    ]
    
    for package in packages:
        try:
            print(f"   Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"   ✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to install {package}: {e}")
            return False
    
    return True

def setup_api_keys():
    """Setup API keys using the secure key manager"""
    print("\n🔐 Setting up API keys...")
    
    try:
        # Import and run the secure key manager
        sys.path.insert(0, str(Path("config")))
        from secure_key_manager import SecureKeyManager
        
        key_manager = SecureKeyManager()
        
        # Check if keys already exist
        is_valid, result = key_manager.validate_keys()
        
        if is_valid:
            print("✅ API keys are already configured and valid!")
            return True
        
        # Setup keys interactively
        if key_manager.setup_keys_interactive():
            print("✅ API keys configured successfully!")
            return True
        else:
            print("❌ API key setup failed.")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import secure key manager: {e}")
        return False
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

def setup_configuration():
    """Setup additional configuration"""
    print("\n⚙️  Setting up additional configuration...")
    
    try:
        # Import and run the enhanced config manager
        sys.path.insert(0, str(Path("config")))
        from enhanced_config_manager import EnhancedConfigManager
        
        config_manager = EnhancedConfigManager()
        
        # Run interactive setup
        if config_manager.setup_interactive():
            print("✅ Configuration setup completed!")
            return True
        else:
            print("❌ Configuration setup failed.")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import enhanced config manager: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration setup failed: {e}")
        return False

def verify_setup():
    """Verify the complete setup"""
    print("\n🔍 Verifying setup...")
    
    try:
        # Import and verify configuration
        sys.path.insert(0, str(Path("config")))
        from enhanced_config_manager import EnhancedConfigManager
        
        config_manager = EnhancedConfigManager()
        is_valid, result = config_manager.validate_configuration()
        
        if is_valid:
            print("✅ Setup verification successful!")
            print("🎉 Your AI Terminal is ready to use!")
            return True
        else:
            print("❌ Setup verification failed:")
            for error in result['errors']:
                print(f"   - {error}")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import enhanced config manager: {e}")
        return False
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def show_next_steps():
    """Show next steps for the user"""
    print("\n🚀 Next Steps:")
    print("=" * 30)
    print("1. Start the AI Terminal:")
    print("   ./start_project.sh")
    print("")
    print("2. Access the web interface:")
    print("   http://localhost:5000")
    print("   Login: admin / admin123")
    print("")
    print("3. Use the terminal directly:")
    print("   python3 main.py")
    print("")
    print("4. Manage your configuration:")
    print("   python3 config/enhanced_config_manager.py status")
    print("   python3 config/enhanced_config_manager.py validate")
    print("")
    print("5. Manage your API keys:")
    print("   python3 config/secure_key_manager.py status")
    print("   python3 config/secure_key_manager.py rotate")
    print("")
    print("📚 For more information, see README.md and SETUP.md")

def main():
    """Main setup function"""
    print("🚀 AI Terminal API Key Setup")
    print("=" * 40)
    print("This script will help you configure your AI Terminal project.")
    print("It will securely store your API keys and configure the system.\n")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please fix the issues above.")
        return False
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install required packages.")
        return False
    
    # Setup API keys
    if not setup_api_keys():
        print("\n❌ API key setup failed.")
        return False
    
    # Setup additional configuration
    if not setup_configuration():
        print("\n❌ Configuration setup failed.")
        return False
    
    # Verify setup
    if not verify_setup():
        print("\n❌ Setup verification failed.")
        return False
    
    # Show next steps
    show_next_steps()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 Setup completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Setup failed. Please check the errors above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)