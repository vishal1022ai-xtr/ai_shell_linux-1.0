# 🔐 Secure API Key Management Guide

## Overview

The AI Terminal project now includes a **robust and secure API key management system** that allows users to:

- **Input API keys once** and have them automatically stored securely
- **Never worry about accidentally committing keys** to version control
- **Use multiple secure storage backends** with automatic fallback
- **Rotate and manage keys** easily
- **Validate key formats** automatically

---

## 🚀 Quick Start

### 1. **Automatic Setup (Recommended)**

Run the setup script from your project root:

```bash
python3 setup_api_keys.py
```

This script will:
- ✅ Check dependencies
- ✅ Install required packages
- ✅ Guide you through API key setup
- ✅ Configure system settings
- ✅ Verify everything works

### 2. **Manual Setup**

If you prefer manual setup:

```bash
# Install dependencies
pip install keyring cryptography

# Setup API keys
python3 config/secure_key_manager.py setup

# Setup configuration
python3 config/enhanced_config_manager.py setup
```

---

## 🔧 How It Works

### **Storage Backends (in order of preference)**

1. **🔐 System Keyring** (Most Secure)
   - Uses your system's built-in keyring (macOS Keychain, Windows Credential Manager, Linux Secret Service)
   - Keys are encrypted and stored by the operating system
   - No additional passwords needed

2. **🔒 Encrypted File Storage** (Very Secure)
   - Encrypts keys with a password you choose
   - Uses strong cryptography (PBKDF2 + Fernet)
   - Keys are stored in encrypted files

3. **📁 Simple File Storage** (Basic Security)
   - Base64 encoded storage (fallback option)
   - Less secure but always available
   - Good for development/testing

### **Automatic Key Loading**

The system automatically tries to load keys in this order:
1. **Secure Storage** (keyring/encrypted)
2. **Config File** (if secure storage unavailable)
3. **Environment Variables** (as fallback)

---

## 📋 Available Commands

### **Secure Key Manager**

```bash
# Setup API keys interactively
python3 config/secure_key_manager.py setup

# Check key status
python3 config/secure_key_manager.py status

# Validate keys
python3 config/secure_key_manager.py validate

# Rotate/update a key
python3 config/secure_key_manager.py rotate

# Clear all stored keys
python3 config/secure_key_manager.py clear
```

### **Enhanced Config Manager**

```bash
# Interactive configuration setup
python3 config/enhanced_config_manager.py setup

# Validate configuration
python3 config/enhanced_config_manager.py validate

# Show configuration status
python3 config/enhanced_config_manager.py status

# Export as environment variables
python3 config/enhanced_config_manager.py export
```

---

## 🔑 API Key Setup Process

### **Step 1: Get Your API Keys**

- **Groq API Key**: https://console.groq.com/keys
- **Gemini API Key**: https://aistudio.google.com/app/apikey

### **Step 2: Run Setup**

```bash
python3 setup_api_keys.py
```

### **Step 3: Enter Keys Securely**

The system will prompt you for each key:
- Keys are hidden while typing (using `getpass`)
- Format validation happens automatically
- Keys are stored securely immediately

### **Step 4: Verify Setup**

```bash
python3 config/secure_key_manager.py status
```

---

## 🛡️ Security Features

### **Key Validation**

- **Groq API Key**: `gsk_` + 48 alphanumeric characters
- **Gemini API Key**: `AIza` + 35 alphanumeric characters
- **Format checking** prevents invalid keys
- **Length validation** ensures proper keys

### **Secure Storage**

- **No plain text storage** anywhere
- **Encryption at rest** for file storage
- **System keyring integration** for maximum security
- **Automatic fallback** to less secure methods if needed

### **Access Control**

- **Local storage only** - keys never leave your machine
- **Process isolation** - keys are not shared between processes
- **User-specific storage** - keys are tied to your user account

---

## 🔄 Key Management

### **Rotating Keys**

```bash
python3 config/secure_key_manager.py rotate
```

This will:
1. Show available keys to rotate
2. Guide you through getting a new key
3. Validate the new key format
4. Store it securely
5. Update the configuration

### **Checking Key Status**

```bash
python3 config/secure_key_manager.py status
```

Shows:
- Which keys are configured
- Masked versions of keys (for security)
- Overall configuration status

### **Clearing Keys**

```bash
python3 config/secure_key_manager.py clear
```

⚠️ **Warning**: This permanently removes all stored keys!

---

## ⚙️ Configuration Management

### **System Configuration**

The enhanced config manager handles:
- **AI Model Settings**: Model names, default preferences
- **System Settings**: Max tokens, temperature, safety mode
- **Web Interface**: Host, port, debug mode, secret keys

### **Interactive Setup**

```bash
python3 config/enhanced_config_manager.py setup
```

Guides you through:
- API key configuration
- System parameter setup
- Web interface configuration
- Security settings

---

## 🐛 Troubleshooting

### **Common Issues**

#### **1. "keyring not available"**
```bash
# Install keyring
pip install keyring

# On Linux, you might also need:
sudo apt-get install libsecret-1-dev
pip install secretstorage
```

#### **2. "cryptography not available"**
```bash
# Install cryptography
pip install cryptography

# On some systems, you might need:
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev
```

#### **3. "Permission denied" errors**
```bash
# Check file permissions
ls -la config/

# Fix permissions if needed
chmod 755 config/
chmod 644 config/*.py
```

#### **4. Keys not loading**
```bash
# Check key status
python3 config/secure_key_manager.py status

# Re-setup if needed
python3 config/secure_key_manager.py setup
```

### **Debug Mode**

Enable debug logging:
```bash
export PYTHONPATH=config:$PYTHONPATH
python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from secure_key_manager import SecureKeyManager
sm = SecureKeyManager()
print('Keys:', sm.get_all_keys())
"
```

---

## 🔒 Security Best Practices

### **Do's**
- ✅ **Use the setup script** for initial configuration
- ✅ **Rotate keys regularly** (every 90 days)
- ✅ **Use strong encryption passwords** if prompted
- ✅ **Keep your system updated** for security patches
- ✅ **Use environment variables** in production

### **Don'ts**
- ❌ **Never commit API keys** to version control
- ❌ **Don't share your encryption passwords**
- ❌ **Avoid using simple file storage** in production
- ❌ **Don't store keys in plain text files**
- ❌ **Avoid using the same keys** across multiple projects

---

## 🌐 Environment Variables

### **Automatic Export**

```bash
python3 config/enhanced_config_manager.py export
```

This generates:
```bash
export AI_TERMINAL_GROQ_API_KEY='your_groq_key_here'
export AI_TERMINAL_GEMINI_API_KEY='your_gemini_key_here'
export AI_TERMINAL_SYSTEM_MAX_TOKENS='4096'
export AI_TERMINAL_SYSTEM_TEMPERATURE='0.7'
```

### **Manual Environment Setup**

Add to your `~/.bashrc` or `~/.zshrc`:
```bash
# AI Terminal Configuration
export AI_TERMINAL_GROQ_API_KEY='your_groq_key_here'
export AI_TERMINAL_GEMINI_API_KEY='your_gemini_key_here'
```

---

## 📱 Integration with AI Terminal

### **Automatic Loading**

The AI Terminal automatically:
- ✅ **Loads keys** from secure storage
- ✅ **Falls back** to config file if needed
- ✅ **Uses environment variables** as last resort
- ✅ **Validates keys** before use
- ✅ **Provides clear error messages** if keys are missing

### **No Code Changes Needed**

Your existing AI Terminal code will work automatically:
- The `EnhancedConfigManager` replaces the old config manager
- API keys are loaded transparently
- All existing functionality preserved

---

## 🧪 Testing Your Setup

### **Quick Test**

```bash
# Test key loading
python3 -c "
import sys
sys.path.insert(0, 'config')
from enhanced_config_manager import EnhancedConfigManager
cm = EnhancedConfigManager()
keys = cm.get_all_api_keys()
print('Keys loaded:', bool(keys['groq_api_key'] and keys['gemini_api_key']))
"
```

### **Full Project Test**

```bash
# Run the complete test suite
python3 test_full_project.py
```

### **Web Interface Test**

```bash
# Start the web interface
./start_project.sh

# Access at http://localhost:5000
# Login: admin / admin123
```

---

## 🔄 Migration from Old System

### **If you have existing config files**

1. **Backup your current config**:
   ```bash
   cp config/ultra_config.ini config/ultra_config.ini.backup
   ```

2. **Run the new setup**:
   ```bash
   python3 setup_api_keys.py
   ```

3. **Verify migration**:
   ```bash
   python3 config/enhanced_config_manager.py validate
   ```

### **If you have environment variables**

The system will automatically detect and use them. No migration needed!

---

## 📚 Advanced Usage

### **Custom Storage Backends**

You can extend the system with custom storage backends:

```python
from config.secure_key_manager import SecureKeyManager

class CustomStorage:
    def store_keys(self, keys):
        # Your custom storage logic
        pass
    
    def get_key(self, key_name):
        # Your custom retrieval logic
        pass

# Add to key manager
key_manager = SecureKeyManager()
key_manager.storage_backends.insert(0, CustomStorage())
```

### **Programmatic Key Management**

```python
from config.secure_key_manager import SecureKeyManager

# Initialize
key_manager = SecureKeyManager()

# Store keys programmatically
keys = {
    'groq_api_key': 'your_key_here',
    'gemini_api_key': 'your_key_here'
}
key_manager._store_keys(keys)

# Retrieve keys
groq_key = key_manager.get_key('groq_api_key')
```

---

## 🆘 Getting Help

### **Check the logs**

```bash
# Enable debug logging
export PYTHONPATH=config:$PYTHONPATH
python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from secure_key_manager import SecureKeyManager
sm = SecureKeyManager()
"
```

### **Common error messages**

- **"No module named 'keyring'"** → Install with `pip install keyring`
- **"keyring.backend.InvalidKeyring"** → System keyring not available, will use encrypted file storage
- **"cryptography.fernet.InvalidToken"** → Wrong encryption password
- **"Permission denied"** → Check file permissions

### **Support**

- 📖 **Documentation**: README.md, SETUP.md
- 🧪 **Tests**: test_full_project.py, error_check_test.py
- 🔧 **Examples**: See the code comments and docstrings

---

## 🎉 Success Indicators

Your setup is successful when:

✅ **Keys are stored securely** (no plain text files)
✅ **AI Terminal starts without key errors**
✅ **Web interface loads and authenticates**
✅ **API calls work successfully**
✅ **Configuration validation passes**

---

## 🔮 Future Enhancements

Planned improvements:
- 🔐 **Hardware security module (HSM) support**
- 🌐 **Cloud key management integration**
- 🔄 **Automatic key rotation**
- 📊 **Usage analytics and monitoring**
- 🚀 **Multi-user key management**

---

*This guide covers the complete secure key management system. For additional help, see the project documentation or run the setup script with `--help` for more options.*