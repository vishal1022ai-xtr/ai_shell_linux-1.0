#!/usr/bin/env python3
"""
Secure API Key Manager for AI Terminal Project
==============================================

This module provides a secure way to manage API keys locally:
- Interactive key input with validation
- Secure local storage using system keyring
- Automatic key loading and validation
- Fallback to encrypted local file storage
- Key rotation and management capabilities

Author: AI Terminal Project
License: MIT
"""

import os
import sys
import json
import base64
import hashlib
import getpass
import platform
from pathlib import Path
from typing import Dict, Optional, Tuple
import configparser
import logging

# Try to import keyring for secure storage
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

# Try to import cryptography for encryption
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecureKeyManager:
    """
    Secure API Key Manager with multiple storage backends
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Storage backends in order of preference
        self.storage_backends = []
        
        if KEYRING_AVAILABLE:
            self.storage_backends.append(KeyringStorage())
        
        if CRYPTO_AVAILABLE:
            self.storage_backends.append(EncryptedFileStorage(self.config_dir))
        
        # Fallback to simple file storage (less secure)
        self.storage_backends.append(SimpleFileStorage(self.config_dir))
        
        # Key validation patterns
        self.key_patterns = {
            'groq_api_key': r'^gsk_[a-zA-Z0-9]{48}$',
            'gemini_api_key': r'^AIza[0-9A-Za-z\-_]{35}$',
            'openai_api_key': r'^sk-[a-zA-Z0-9]{48}$',
            'anthropic_api_key': r'^sk-ant-[a-zA-Z0-9]{48}$'
        }
        
        # Required keys for the project
        self.required_keys = ['groq_api_key', 'gemini_api_key']
        
    def setup_keys_interactive(self) -> bool:
        """
        Interactive setup for API keys
        """
        print("\n🔐 AI Terminal API Key Setup")
        print("=" * 50)
        print("This will securely store your API keys for local use.")
        print("Keys are stored locally and never shared.\n")
        
        # Check if keys already exist
        existing_keys = self.get_all_keys()
        if existing_keys:
            print("📋 Existing keys found:")
            for key_name, key_value in existing_keys.items():
                if key_value:
                    masked_key = self._mask_key(key_value)
                    print(f"  {key_name}: {masked_key}")
            
            response = input("\n❓ Do you want to update existing keys? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("✅ Keeping existing keys.")
                return True
        
        # Collect new keys
        new_keys = {}
        for key_name in self.required_keys:
            print(f"\n🔑 Setting up {key_name}:")
            
            # Get key from user
            if key_name == 'groq_api_key':
                print("   Get your Groq API key from: https://console.groq.com/keys")
                print("   Format: gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
            elif key_name == 'gemini_api_key':
                print("   Get your Gemini API key from: https://aistudio.google.com/app/apikey")
                print("   Format: AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
            
            while True:
                key_value = getpass.getpass(f"   Enter {key_name}: ").strip()
                
                if not key_value:
                    print("   ⚠️  Key cannot be empty. Please try again.")
                    continue
                
                # Validate key format
                if self._validate_key_format(key_name, key_value):
                    new_keys[key_name] = key_value
                    print(f"   ✅ {key_name} format validated")
                    break
                else:
                    print(f"   ❌ Invalid {key_name} format. Please check and try again.")
        
        # Store keys securely
        if self._store_keys(new_keys):
            print("\n🎉 API keys stored successfully!")
            print("✅ Your AI Terminal is now configured and ready to use.")
            return True
        else:
            print("\n❌ Failed to store API keys securely.")
            return False
    
    def get_key(self, key_name: str) -> Optional[str]:
        """
        Retrieve a specific API key
        """
        for backend in self.storage_backends:
            try:
                key = backend.get_key(key_name)
                if key:
                    return key
            except Exception as e:
                logger.warning(f"Backend {backend.__class__.__name__} failed: {e}")
                continue
        
        return None
    
    def get_all_keys(self) -> Dict[str, Optional[str]]:
        """
        Retrieve all stored API keys
        """
        all_keys = {}
        for key_name in self.required_keys:
            all_keys[key_name] = self.get_key(key_name)
        return all_keys
    
    def validate_keys(self) -> Tuple[bool, Dict[str, str]]:
        """
        Validate all required keys are present and valid
        """
        missing_keys = []
        invalid_keys = []
        valid_keys = {}
        
        for key_name in self.required_keys:
            key_value = self.get_key(key_name)
            
            if not key_value:
                missing_keys.append(key_name)
            elif not self._validate_key_format(key_name, key_value):
                invalid_keys.append(key_name)
            else:
                valid_keys[key_name] = key_value
        
        if missing_keys or invalid_keys:
            return False, {
                'missing': missing_keys,
                'invalid': invalid_keys,
                'valid': valid_keys
            }
        
        return True, valid_keys
    
    def rotate_key(self, key_name: str) -> bool:
        """
        Rotate/update a specific API key
        """
        print(f"\n🔄 Rotating {key_name}")
        
        if key_name == 'groq_api_key':
            print("   Get your new Groq API key from: https://console.groq.com/keys")
        elif key_name == 'gemini_api_key':
            print("   Get your new Gemini API key from: https://aistudio.google.com/app/apikey")
        
        new_key = getpass.getpass(f"   Enter new {key_name}: ").strip()
        
        if not new_key:
            print("   ❌ Key cannot be empty.")
            return False
        
        if not self._validate_key_format(key_name, new_key):
            print(f"   ❌ Invalid {key_name} format.")
            return False
        
        # Store the new key
        if self._store_keys({key_name: new_key}):
            print(f"   ✅ {key_name} rotated successfully!")
            return True
        else:
            print(f"   ❌ Failed to rotate {key_name}.")
            return False
    
    def clear_all_keys(self) -> bool:
        """
        Clear all stored API keys
        """
        print("\n🗑️  Clearing all stored API keys...")
        
        for backend in self.storage_backends:
            try:
                backend.clear_all_keys()
            except Exception as e:
                logger.warning(f"Failed to clear keys from {backend.__class__.__name__}: {e}")
        
        print("✅ All API keys cleared.")
        return True
    
    def _store_keys(self, keys: Dict[str, str]) -> bool:
        """
        Store keys using the best available backend
        """
        for backend in self.storage_backends:
            try:
                if backend.store_keys(keys):
                    logger.info(f"Keys stored successfully using {backend.__class__.__name__}")
                    return True
            except Exception as e:
                logger.warning(f"Backend {backend.__class__.__name__} failed: {e}")
                continue
        
        return False
    
    def _validate_key_format(self, key_name: str, key_value: str) -> bool:
        """
        Validate key format using regex patterns
        """
        import re
        
        if key_name in self.key_patterns:
            pattern = self.key_patterns[key_name]
            return bool(re.match(pattern, key_value))
        
        # If no pattern defined, just check it's not empty
        return bool(key_value and len(key_value) > 10)
    
    def _mask_key(self, key: str) -> str:
        """
        Mask a key for display (show first 8 and last 4 characters)
        """
        if len(key) <= 12:
            return "*" * len(key)
        return key[:8] + "*" * (len(key) - 12) + key[-4:]


class KeyringStorage:
    """
    Secure storage using system keyring
    """
    
    def __init__(self):
        self.service_name = "ai_terminal"
        self.username = "api_keys"
    
    def store_keys(self, keys: Dict[str, str]) -> bool:
        """Store keys in system keyring"""
        try:
            # Store as JSON in a single keyring entry
            key_data = json.dumps(keys)
            keyring.set_password(self.service_name, self.username, key_data)
            return True
        except Exception as e:
            logger.error(f"Keyring storage failed: {e}")
            return False
    
    def get_key(self, key_name: str) -> Optional[str]:
        """Retrieve a key from system keyring"""
        try:
            key_data = keyring.get_password(self.service_name, self.username)
            if key_data:
                keys = json.loads(key_data)
                return keys.get(key_name)
        except Exception as e:
            logger.error(f"Keyring retrieval failed: {e}")
        return None
    
    def clear_all_keys(self) -> bool:
        """Clear all keys from system keyring"""
        try:
            keyring.delete_password(self.service_name, self.username)
            return True
        except Exception as e:
            logger.error(f"Keyring clear failed: {e}")
            return False


class EncryptedFileStorage:
    """
    Encrypted file storage using cryptography
    """
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.keys_file = config_dir / ".encrypted_keys"
        self.salt_file = config_dir / ".salt"
        self._ensure_salt()
    
    def _ensure_salt(self):
        """Ensure salt file exists"""
        if not self.salt_file.exists():
            salt = os.urandom(16)
            self.salt_file.write_bytes(salt)
    
    def _get_encryption_key(self, password: str) -> bytes:
        """Derive encryption key from password"""
        salt = self.salt_file.read_bytes()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def store_keys(self, keys: Dict[str, str]) -> bool:
        """Store keys in encrypted file"""
        try:
            # Get encryption password from user
            password = getpass.getpass("🔐 Enter encryption password for local storage: ").strip()
            if not password:
                return False
            
            # Encrypt and store
            key = self._get_encryption_key(password)
            f = Fernet(key)
            encrypted_data = f.encrypt(json.dumps(keys).encode())
            self.keys_file.write_bytes(encrypted_data)
            return True
        except Exception as e:
            logger.error(f"Encrypted storage failed: {e}")
            return False
    
    def get_key(self, key_name: str) -> Optional[str]:
        """Retrieve a key from encrypted file"""
        try:
            if not self.keys_file.exists():
                return None
            
            # Get decryption password from user
            password = getpass.getpass("🔐 Enter encryption password: ").strip()
            if not password:
                return None
            
            # Decrypt and retrieve
            key = self._get_encryption_key(password)
            f = Fernet(key)
            encrypted_data = self.keys_file.read_bytes()
            decrypted_data = f.decrypt(encrypted_data)
            keys = json.loads(decrypted_data.decode())
            return keys.get(key_name)
        except Exception as e:
            logger.error(f"Encrypted retrieval failed: {e}")
        return None
    
    def clear_all_keys(self) -> bool:
        """Clear encrypted keys file"""
        try:
            if self.keys_file.exists():
                self.keys_file.unlink()
            return True
        except Exception as e:
            logger.error(f"Encrypted clear failed: {e}")
            return False


class SimpleFileStorage:
    """
    Simple file storage (less secure, fallback option)
    """
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.keys_file = config_dir / ".local_keys"
    
    def store_keys(self, keys: Dict[str, str]) -> bool:
        """Store keys in simple file"""
        try:
            # Create a simple encrypted-like storage
            encoded_keys = {}
            for key_name, key_value in keys.items():
                # Simple base64 encoding (not truly secure)
                encoded_keys[key_name] = base64.b64encode(key_value.encode()).decode()
            
            self.keys_file.write_text(json.dumps(encoded_keys, indent=2))
            return True
        except Exception as e:
            logger.error(f"Simple storage failed: {e}")
            return False
    
    def get_key(self, key_name: str) -> Optional[str]:
        """Retrieve a key from simple file"""
        try:
            if not self.keys_file.exists():
                return None
            
            encoded_keys = json.loads(self.keys_file.read_text())
            encoded_value = encoded_keys.get(key_name)
            if encoded_value:
                return base64.b64decode(encoded_value).decode()
        except Exception as e:
            logger.error(f"Simple retrieval failed: {e}")
        return None
    
    def clear_all_keys(self) -> bool:
        """Clear simple keys file"""
        try:
            if self.keys_file.exists():
                self.keys_file.unlink()
            return True
        except Exception as e:
            logger.error(f"Simple clear failed: {e}")
            return False


def main():
    """
    Command-line interface for key management
    """
    key_manager = SecureKeyManager()
    
    if len(sys.argv) < 2:
        print("🔐 AI Terminal API Key Manager")
        print("=" * 40)
        print("Usage:")
        print("  python secure_key_manager.py setup     # Interactive setup")
        print("  python secure_key_manager.py validate  # Validate keys")
        print("  python secure_key_manager.py rotate    # Rotate keys")
        print("  python secure_key_manager.py clear     # Clear all keys")
        print("  python secure_key_manager.py status    # Show key status")
        return
    
    command = sys.argv[1].lower()
    
    if command == "setup":
        key_manager.setup_keys_interactive()
    
    elif command == "validate":
        is_valid, result = key_manager.validate_keys()
        if is_valid:
            print("✅ All API keys are valid and ready!")
        else:
            print("❌ API key validation failed:")
            if result['missing']:
                print(f"   Missing keys: {', '.join(result['missing'])}")
            if result['invalid']:
                print(f"   Invalid keys: {', '.join(result['invalid'])}")
    
    elif command == "rotate":
        print("🔄 Key Rotation")
        print("Available keys to rotate:")
        for i, key_name in enumerate(key_manager.required_keys, 1):
            print(f"  {i}. {key_name}")
        
        try:
            choice = int(input("\nSelect key to rotate (1-{}): ".format(len(key_manager.required_keys))))
            if 1 <= choice <= len(key_manager.required_keys):
                key_name = key_manager.required_keys[choice - 1]
                key_manager.rotate_key(key_name)
            else:
                print("❌ Invalid choice.")
        except ValueError:
            print("❌ Please enter a valid number.")
    
    elif command == "clear":
        response = input("⚠️  Are you sure you want to clear ALL stored API keys? (yes/NO): ").strip()
        if response.lower() == "yes":
            key_manager.clear_all_keys()
        else:
            print("✅ Operation cancelled.")
    
    elif command == "status":
        print("📊 API Key Status")
        print("=" * 30)
        
        all_keys = key_manager.get_all_keys()
        for key_name, key_value in all_keys.items():
            if key_value:
                masked_key = key_manager._mask_key(key_value)
                print(f"  {key_name}: {masked_key} ✅")
            else:
                print(f"  {key_name}: Not set ❌")
        
        is_valid, _ = key_manager.validate_keys()
        print(f"\nOverall Status: {'✅ Ready' if is_valid else '❌ Needs Setup'}")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'python secure_key_manager.py' for help.")


if __name__ == "__main__":
    main()