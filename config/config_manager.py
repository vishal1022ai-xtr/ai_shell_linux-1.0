# config/config_manager.py
import configparser
import os
from pathlib import Path
from rich.console import Console

console = Console()

class ConfigManager:
    """
    Manages configuration for the Unified AI Shell.
    Loads settings from config/ultra_config.ini and provides easy access to configuration values.
    """
    
    def __init__(self, config_file: str = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to the configuration file. Defaults to 'config/ultra_config.ini'
        """
        if config_file is None:
            # Get the directory where this file is located
            current_dir = Path(__file__).parent
            config_file = current_dir / "ultra_config.ini"
        
        self.config_file = Path(config_file)
        self.config = configparser.ConfigParser()
        
        # Load the configuration
        self._load_config()
    
    def _load_config(self):
        """Load configuration from the INI file."""
        try:
            if not self.config_file.exists():
                console.print(f"[bold red]Error: Configuration file not found: {self.config_file}[/bold red]")
                console.print("[yellow]Please ensure the config/ultra_config.ini file exists.[/yellow]")
                raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
            
            self.config.read(self.config_file)
            console.print(f"[green]✓ Configuration loaded from {self.config_file}[/green]")
            
        except Exception as e:
            console.print(f"[bold red]Error loading configuration: {e}[/bold red]")
            raise
    
    def get(self, section: str, key: str, default: str = None) -> str:
        """
        Get a configuration value.
        
        Args:
            section: The section name in the INI file
            key: The key name within the section
            default: Default value if the key doesn't exist
            
        Returns:
            The configuration value as a string
        """
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if default is not None:
                return default
            console.print(f"[yellow]Warning: Configuration key '{section}.{key}' not found, using default: {default}[/yellow]")
            return default
    
    def get_boolean(self, section: str, key: str, default: bool = False) -> bool:
        """
        Get a boolean configuration value.
        
        Args:
            section: The section name in the INI file
            key: The key name within the section
            default: Default value if the key doesn't exist
            
        Returns:
            The configuration value as a boolean
        """
        try:
            return self.config.getboolean(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default
    
    def get_int(self, section: str, key: str, default: int = 0) -> int:
        """
        Get an integer configuration value.
        
        Args:
            section: The section name in the INI file
            key: The key name within the section
            default: Default value if the key doesn't exist
            
        Returns:
            The configuration value as an integer
        """
        try:
            return self.config.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default
    
    def has_section(self, section: str) -> bool:
        """Check if a section exists in the configuration."""
        return self.config.has_section(section)
    
    def has_option(self, section: str, key: str) -> bool:
        """Check if a key exists in a section."""
        return self.config.has_option(section, key)
    
    def get_section(self, section: str) -> dict:
        """
        Get all key-value pairs from a section.
        
        Args:
            section: The section name
            
        Returns:
            Dictionary of key-value pairs in the section
        """
        if not self.config.has_section(section):
            return {}
        
        return dict(self.config.items(section))
    
    def reload(self):
        """Reload the configuration from the file."""
        self._load_config()
    
    def validate_api_keys(self) -> bool:
        """
        Validate that API keys are properly configured.
        
        Returns:
            True if API keys are valid, False otherwise
        """
        groq_key = self.get('API_KEYS', 'groq_api_key', '')
        gemini_key = self.get('API_KEYS', 'gemini_api_key', '')
        
        groq_valid = groq_key and groq_key != 'your_groq_key_here'
        gemini_valid = gemini_key and gemini_key != 'your_gemini_key_here'
        
        if not groq_valid:
            console.print("[yellow]Warning: Groq API key not configured[/yellow]")
        
        if not gemini_valid:
            console.print("[yellow]Warning: Gemini API key not configured[/yellow]")
        
        return groq_valid or gemini_valid
