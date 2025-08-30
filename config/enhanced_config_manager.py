#!/usr/bin/env python3
"""
Enhanced Configuration Manager for AI Terminal Project
====================================================

This module provides enhanced configuration management with:
- Automatic API key loading from secure storage
- Fallback to config file if secure storage unavailable
- Environment variable support
- Configuration validation and auto-setup
- Integration with SecureKeyManager

Author: AI Terminal Project
License: MIT
"""

import os
import sys
import configparser
from pathlib import Path
from typing import Dict, Optional, Any
import logging

# Import the secure key manager
try:
    from .secure_key_manager import SecureKeyManager
    SECURE_KEY_MANAGER_AVAILABLE = True
except ImportError:
    SECURE_KEY_MANAGER_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedConfigManager:
    """
    Enhanced configuration manager with secure key handling
    """
    
    def __init__(self, config_file: str = "config/ultra_config.ini"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(exist_ok=True)
        
        # Initialize secure key manager if available
        self.secure_key_manager = None
        if SECURE_KEY_MANAGER_AVAILABLE:
            try:
                self.secure_key_manager = SecureKeyManager()
            except Exception as e:
                logger.warning(f"Failed to initialize secure key manager: {e}")
        
        # Load configuration
        self.config = configparser.ConfigParser()
        self._load_config()
        
        # Auto-setup if needed
        self._auto_setup_if_needed()
    
    def _load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                self.config.read(self.config_file)
                logger.info(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
                self._create_default_config()
        else:
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration file"""
        self.config['API_KEYS'] = {
            'groq_api_key': 'YOUR_GROQ_API_KEY_HERE',
            'gemini_api_key': 'YOUR_GEMINI_API_KEY_HERE'
        }
        
        self.config['AI_MODELS'] = {
            'default_model': 'auto',
            'groq_model': 'llama3-8b-8192',
            'gemini_model': 'gemini-1.5-flash'
        }
        
        self.config['SYSTEM'] = {
            'max_tokens': '4096',
            'temperature': '0.7',
            'safety_mode': 'enabled',
            'log_level': 'INFO'
        }
        
        self.config['WEB_INTERFACE'] = {
            'host': 'localhost',
            'port': '5000',
            'debug': 'False',
            'secret_key': 'CHANGE_THIS_SECRET_KEY'
        }
        
        self._save_config()
        logger.info(f"Default configuration created at {self.config_file}")
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config file: {e}")
    
    def _auto_setup_if_needed(self):
        """Auto-setup API keys if they're not configured"""
        if not self._has_valid_api_keys():
            logger.info("API keys not configured. Starting auto-setup...")
            self._auto_setup_api_keys()
    
    def _has_valid_api_keys(self) -> bool:
        """Check if valid API keys are available"""
        groq_key = self.get_api_key('groq_api_key')
        gemini_key = self.get_api_key('gemini_api_key')
        
        return (groq_key and groq_key != 'YOUR_GROQ_API_KEY_HERE' and
                gemini_key and gemini_key != 'YOUR_GEMINI_API_KEY_HERE')
    
    def _auto_setup_api_keys(self):
        """Automatically setup API keys using secure storage"""
        if not self.secure_key_manager:
            logger.warning("Secure key manager not available. Manual setup required.")
            return False
        
        try:
            # Check if keys exist in secure storage
            is_valid, result = self.secure_key_manager.validate_keys()
            
            if is_valid:
                logger.info("Valid API keys found in secure storage. Loading...")
                self._load_keys_from_secure_storage()
                return True
            else:
                logger.info("API keys not found in secure storage. Starting interactive setup...")
                return self.secure_key_manager.setup_keys_interactive()
                
        except Exception as e:
            logger.error(f"Auto-setup failed: {e}")
            return False
    
    def _load_keys_from_secure_storage(self):
        """Load API keys from secure storage and update config"""
        if not self.secure_key_manager:
            return
        
        try:
            all_keys = self.secure_key_manager.get_all_keys()
            
            for key_name, key_value in all_keys.items():
                if key_value:
                    # Update config file
                    if 'API_KEYS' not in self.config:
                        self.config['API_KEYS'] = {}
                    
                    self.config['API_KEYS'][key_name] = key_value
                    logger.info(f"Loaded {key_name} from secure storage")
            
            # Save updated config
            self._save_config()
            
        except Exception as e:
            logger.error(f"Failed to load keys from secure storage: {e}")
    
    def get_api_key(self, key_name: str) -> Optional[str]:
        """
        Get API key with priority: Secure Storage > Config File > Environment Variable
        """
        # Try secure storage first
        if self.secure_key_manager:
            try:
                key = self.secure_key_manager.get_key(key_name)
                if key:
                    return key
            except Exception as e:
                logger.debug(f"Secure storage failed for {key_name}: {e}")
        
        # Try config file
        try:
            if 'API_KEYS' in self.config and key_name in self.config['API_KEYS']:
                key = self.config['API_KEYS'][key_name]
                if key and key != f'YOUR_{key_name.upper()}_HERE':
                    return key
        except Exception as e:
            logger.debug(f"Config file failed for {key_name}: {e}")
        
        # Try environment variable
        env_key = f"AI_TERMINAL_{key_name.upper()}"
        key = os.getenv(env_key)
        if key:
            return key
        
        return None
    
    def get_config(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        try:
            if section in self.config and key in self.config[section]:
                value = self.config[section][key]
                
                # Convert boolean strings
                if value.lower() in ['true', 'false']:
                    return value.lower() == 'true'
                
                # Convert numeric strings
                try:
                    if '.' in value:
                        return float(value)
                    else:
                        return int(value)
                except ValueError:
                    pass
                
                return value
        except Exception as e:
            logger.debug(f"Failed to get config {section}.{key}: {e}")
        
        return default
    
    def set_config(self, section: str, key: str, value: Any):
        """Set configuration value"""
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = str(value)
        self._save_config()
    
    def get_all_api_keys(self) -> Dict[str, Optional[str]]:
        """Get all API keys"""
        keys = {}
        for key_name in ['groq_api_key', 'gemini_api_key']:
            keys[key_name] = self.get_api_key(key_name)
        return keys
    
    def validate_configuration(self) -> tuple[bool, Dict[str, Any]]:
        """Validate the complete configuration"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'api_keys': {},
            'system_config': {},
            'web_config': {}
        }
        
        # Validate API keys
        api_keys = self.get_all_api_keys()
        validation_result['api_keys'] = api_keys
        
        for key_name, key_value in api_keys.items():
            if not key_value or key_value.startswith('YOUR_'):
                validation_result['errors'].append(f"Missing or invalid {key_name}")
                validation_result['valid'] = False
        
        # Validate system configuration
        system_config = {}
        for key in ['max_tokens', 'temperature', 'safety_mode', 'log_level']:
            value = self.get_config('SYSTEM', key)
            system_config[key] = value
            
            if key == 'max_tokens' and (not value or value < 1):
                validation_result['warnings'].append(f"Invalid {key}: {value}")
            elif key == 'temperature' and (not value or value < 0 or value > 2):
                validation_result['warnings'].append(f"Invalid {key}: {value}")
        
        validation_result['system_config'] = system_config
        
        # Validate web configuration
        web_config = {}
        for key in ['host', 'port', 'debug', 'secret_key']:
            value = self.get_config('WEB_INTERFACE', key)
            web_config[key] = value
            
            if key == 'port' and (not value or value < 1 or value > 65535):
                validation_result['warnings'].append(f"Invalid {key}: {value}")
            elif key == 'secret_key' and value == 'CHANGE_THIS_SECRET_KEY':
                validation_result['warnings'].append(f"Default {key} should be changed")
        
        validation_result['web_config'] = web_config
        
        return validation_result['valid'], validation_result
    
    def setup_interactive(self) -> bool:
        """Interactive configuration setup"""
        print("\n🔧 AI Terminal Configuration Setup")
        print("=" * 50)
        
        # Setup API keys
        if self.secure_key_manager:
            print("\n🔐 Setting up API keys...")
            if self.secure_key_manager.setup_keys_interactive():
                self._load_keys_from_secure_storage()
                print("✅ API keys configured successfully!")
            else:
                print("❌ API key setup failed.")
                return False
        else:
            print("\n⚠️  Secure key manager not available.")
            print("   Please manually edit config/ultra_config.ini")
            return False
        
        # Setup system configuration
        print("\n⚙️  Setting up system configuration...")
        self._setup_system_config()
        
        # Setup web interface configuration
        print("\n🌐 Setting up web interface configuration...")
        self._setup_web_config()
        
        print("\n🎉 Configuration setup completed!")
        return True
    
    def _setup_system_config(self):
        """Interactive system configuration setup"""
        print("   System Configuration:")
        
        # Max tokens
        while True:
            try:
                max_tokens = input("   Max tokens (default: 4096): ").strip()
                if not max_tokens:
                    max_tokens = 4096
                else:
                    max_tokens = int(max_tokens)
                    if max_tokens < 1:
                        print("     ⚠️  Max tokens must be at least 1")
                        continue
                break
            except ValueError:
                print("     ⚠️  Please enter a valid number")
        
        self.set_config('SYSTEM', 'max_tokens', max_tokens)
        
        # Temperature
        while True:
            try:
                temperature = input("   Temperature (0.0-2.0, default: 0.7): ").strip()
                if not temperature:
                    temperature = 0.7
                else:
                    temperature = float(temperature)
                    if temperature < 0 or temperature > 2:
                        print("     ⚠️  Temperature must be between 0.0 and 2.0")
                        continue
                break
            except ValueError:
                print("     ⚠️  Please enter a valid number")
        
        self.set_config('SYSTEM', 'temperature', temperature)
        
        # Safety mode
        safety_mode = input("   Enable safety mode? (y/N): ").strip().lower()
        self.set_config('SYSTEM', 'safety_mode', safety_mode in ['y', 'yes'])
        
        # Log level
        log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        print(f"   Available log levels: {', '.join(log_levels)}")
        log_level = input("   Log level (default: INFO): ").strip().upper()
        if not log_level or log_level not in log_levels:
            log_level = 'INFO'
        self.set_config('SYSTEM', 'log_level', log_level)
    
    def _setup_web_config(self):
        """Interactive web interface configuration setup"""
        print("   Web Interface Configuration:")
        
        # Host
        host = input("   Host (default: localhost): ").strip()
        if not host:
            host = 'localhost'
        self.set_config('WEB_INTERFACE', 'host', host)
        
        # Port
        while True:
            try:
                port = input("   Port (default: 5000): ").strip()
                if not port:
                    port = 5000
                else:
                    port = int(port)
                    if port < 1 or port > 65535:
                        print("     ⚠️  Port must be between 1 and 65535")
                        continue
                break
            except ValueError:
                print("     ⚠️  Please enter a valid number")
        
        self.set_config('WEB_INTERFACE', 'port', port)
        
        # Debug mode
        debug = input("   Enable debug mode? (y/N): ").strip().lower()
        self.set_config('WEB_INTERFACE', 'debug', debug in ['y', 'yes'])
        
        # Secret key
        import secrets
        secret_key = secrets.token_hex(32)
        print(f"   Generated secret key: {secret_key[:16]}...")
        self.set_config('WEB_INTERFACE', 'secret_key', secret_key)
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI-specific configuration"""
        return {
            'groq_api_key': self.get_api_key('groq_api_key'),
            'gemini_api_key': self.get_api_key('gemini_api_key'),
            'default_model': self.get_config('AI_MODELS', 'default_model', 'auto'),
            'groq_model': self.get_config('AI_MODELS', 'groq_model', 'llama3-8b-8192'),
            'gemini_model': self.get_config('AI_MODELS', 'gemini_model', 'gemini-1.5-flash'),
            'max_tokens': self.get_config('SYSTEM', 'max_tokens', 4096),
            'temperature': self.get_config('SYSTEM', 'temperature', 0.7),
            'safety_mode': self.get_config('SYSTEM', 'safety_mode', True)
        }
    
    def get_web_config(self) -> Dict[str, Any]:
        """Get web interface configuration"""
        return {
            'host': self.get_config('WEB_INTERFACE', 'host', 'localhost'),
            'port': self.get_config('WEB_INTERFACE', 'port', 5000),
            'debug': self.get_config('WEB_INTERFACE', 'debug', False),
            'secret_key': self.get_config('WEB_INTERFACE', 'secret_key', 'CHANGE_THIS_SECRET_KEY')
        }
    
    def export_env_vars(self):
        """Export configuration as environment variables"""
        env_vars = {}
        
        # Export API keys
        api_keys = self.get_all_api_keys()
        for key_name, key_value in api_keys.items():
            if key_value:
                env_key = f"AI_TERMINAL_{key_name.upper()}"
                env_vars[env_key] = key_value
        
        # Export system config
        for key in ['max_tokens', 'temperature', 'safety_mode', 'log_level']:
            value = self.get_config('SYSTEM', key)
            if value is not None:
                env_key = f"AI_TERMINAL_SYSTEM_{key.upper()}"
                env_vars[env_key] = str(value)
        
        return env_vars


def main():
    """
    Command-line interface for enhanced configuration management
    """
    config_manager = EnhancedConfigManager()
    
    if len(sys.argv) < 2:
        print("🔧 AI Terminal Enhanced Configuration Manager")
        print("=" * 55)
        print("Usage:")
        print("  python enhanced_config_manager.py setup     # Interactive setup")
        print("  python enhanced_config_manager.py validate  # Validate configuration")
        print("  python enhanced_config_manager.py status    # Show configuration status")
        print("  python enhanced_config_manager.py export    # Export as environment variables")
        return
    
    command = sys.argv[1].lower()
    
    if command == "setup":
        config_manager.setup_interactive()
    
    elif command == "validate":
        is_valid, result = config_manager.validate_configuration()
        
        print("📊 Configuration Validation Results")
        print("=" * 40)
        
        if is_valid:
            print("✅ Configuration is valid!")
        else:
            print("❌ Configuration has errors:")
            for error in result['errors']:
                print(f"   - {error}")
        
        if result['warnings']:
            print("\n⚠️  Warnings:")
            for warning in result['warnings']:
                print(f"   - {warning}")
        
        print(f"\n🔑 API Keys:")
        for key_name, key_value in result['api_keys'].items():
            if key_value and not key_value.startswith('YOUR_'):
                masked_key = key_value[:8] + "*" * (len(key_value) - 12) + key_value[-4:] if len(key_value) > 12 else "*" * len(key_value)
                print(f"   {key_name}: {masked_key} ✅")
            else:
                print(f"   {key_name}: Not configured ❌")
    
    elif command == "status":
        print("📊 Configuration Status")
        print("=" * 30)
        
        # API Keys status
        api_keys = config_manager.get_all_api_keys()
        print("🔑 API Keys:")
        for key_name, key_value in api_keys.items():
            if key_value and not key_value.startswith('YOUR_'):
                masked_key = key_value[:8] + "*" * (len(key_value) - 12) + key_value[-4:] if len(key_value) > 12 else "*" * len(key_value)
                print(f"   {key_name}: {masked_key} ✅")
            else:
                print(f"   {key_name}: Not configured ❌")
        
        # System config status
        print("\n⚙️  System Configuration:")
        system_config = config_manager.get_config('SYSTEM', 'max_tokens'), config_manager.get_config('SYSTEM', 'temperature'), config_manager.get_config('SYSTEM', 'safety_mode')
        print(f"   Max tokens: {system_config[0]}")
        print(f"   Temperature: {system_config[1]}")
        print(f"   Safety mode: {system_config[2]}")
        
        # Web config status
        print("\n🌐 Web Interface Configuration:")
        web_config = config_manager.get_web_config()
        print(f"   Host: {web_config['host']}")
        print(f"   Port: {web_config['port']}")
        print(f"   Debug: {web_config['debug']}")
        print(f"   Secret key: {'Configured' if web_config['secret_key'] != 'CHANGE_THIS_SECRET_KEY' else 'Default (should change)'}")
    
    elif command == "export":
        env_vars = config_manager.export_env_vars()
        print("📤 Environment Variables Export")
        print("=" * 35)
        
        if env_vars:
            print("Add these to your environment:")
            for key, value in env_vars.items():
                print(f"export {key}='{value}'")
        else:
            print("No configuration to export.")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'python enhanced_config_manager.py' for help.")


if __name__ == "__main__":
    main()