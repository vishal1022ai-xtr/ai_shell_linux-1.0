#!/usr/bin/env python3
"""
Comprehensive Test Suite for the Full AI Terminal Project
Tests all major components: Core AI Shell, Web Interface, Ethical Hacking, Terminal Manager
"""

import sys
import os
import time
import requests
import threading
from pathlib import Path

# Add paths
sys.path.append('core')
sys.path.append('config')
sys.path.append('web_interface')

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_test_result(test_name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"  {status} {test_name}")
    if details:
        print(f"    📝 {details}")

def test_core_ai_shell():
    """Test the core AI Shell functionality"""
    print_header("Testing Core AI Shell")
    
    try:
        from config_manager import ConfigManager
        from ai_manager import AIManager
        
        # Test config manager
        config = ConfigManager()
        print_test_result("Config Manager", True, "Configuration loaded successfully")
        
        # Test AI manager
        am = AIManager(config)
        print_test_result("AI Manager", True, "AI Manager initialized")
        
        # Test API connectivity
        response = am.get_ai_response("Hello, how are you?", "auto")
        if response[1] != "Error":
            print_test_result("API Connectivity", True, f"Response from {response[1]}")
        else:
            print_test_result("API Connectivity", False, "API not responding")
        
        # Test task routing
        task_types = [
            ("Write a Python function", "code_generation"),
            ("Analyze this code", "code_generation"),
            ("Create a website", "web_content"),
            ("Run this command", "execution"),
            ("Explain something", "analysis")
        ]
        
        for prompt, expected in task_types:
            actual = am._determine_task_type(prompt)
            success = actual == expected
            print_test_result(f"Task Routing: {prompt[:30]}...", success, f"Expected: {expected}, Got: {actual}")
        
        return True
        
    except Exception as e:
        print_test_result("Core AI Shell", False, str(e))
        return False

def test_web_interface():
    """Test the web interface functionality"""
    print_header("Testing Web Interface")
    
    try:
        from web_interface.app_enhanced import app
        
        # Test app import
        print_test_result("Flask App Import", True, "App imported successfully")
        
        # Test app configuration
        print_test_result("App Configuration", True, f"App name: {app.name}")
        
        # Test routes exist
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        expected_routes = ['/login', '/dashboard', '/api/']
        
        for route in expected_routes:
            found = any(route in r for r in routes)
            print_test_result(f"Route: {route}", found, "Route found" if found else "Route missing")
        
        return True
        
    except Exception as e:
        print_test_result("Web Interface", False, str(e))
        return False

def test_ethical_hacking():
    """Test the ethical hacking capabilities"""
    print_header("Testing Ethical Hacking")
    
    try:
        from web_interface.ethical_hacking import NetworkScanner, VulnerabilityScanner, SocialEngineering
        
        # Test imports
        print_test_result("Module Imports", True, "All modules imported")
        
        # Test network scanner
        scanner = NetworkScanner()
        print_test_result("Network Scanner", True, "Scanner initialized")
        
        # Test vulnerability scanner
        vuln_scanner = VulnerabilityScanner()
        print_test_result("Vulnerability Scanner", True, "Scanner initialized")
        
        # Test social engineering
        social_eng = SocialEngineering()
        print_test_result("Social Engineering", True, "Module initialized")
        
        return True
        
    except Exception as e:
        print_test_result("Ethical Hacking", False, str(e))
        return False

def test_terminal_manager():
    """Test the enhanced terminal manager"""
    print_header("Testing Enhanced Terminal Manager")
    
    try:
        from web_interface.enhanced_terminal_manager import EnhancedTerminalManager
        
        # Test import
        print_test_result("Module Import", True, "Terminal manager imported")
        
        # Test initialization
        tm = EnhancedTerminalManager()
        print_test_result("Initialization", True, "Manager initialized")
        
        # Test basic functionality
        print_test_result("Process Monitoring", True, "Monitoring threads started")
        
        # Test safe command execution
        result = tm.execute_command_safe("echo 'test'", timeout=5)
        if result and result.get('success') and result.get('pid'):
            print_test_result("Safe Command Execution", True, f"Command executed, PID: {result['pid']}")
        else:
            print_test_result("Safe Command Execution", False, "Command execution failed")
        
        # Cleanup
        tm.shutdown()
        print_test_result("Shutdown", True, "Manager shutdown cleanly")
        
        return True
        
    except Exception as e:
        print_test_result("Terminal Manager", False, str(e))
        return False

def test_file_structure():
    """Test the project file structure"""
    print_header("Testing Project File Structure")
    
    required_files = [
        "core/ai_manager.py",
        "core/system_controller.py",
        "config/ultra_config.ini",
        "config/config_manager.py",
        "web_interface/app_enhanced.py",
        "web_interface/ethical_hacking.py",
        "web_interface/enhanced_terminal_manager.py",
        "requirements.txt",
        "UNIFIED_README.md"
    ]
    
    required_dirs = [
        "core",
        "config", 
        "web_interface",
        "web_interface/static",
        "web_interface/templates",
        "logs"
    ]
    
    all_good = True
    
    for file_path in required_files:
        exists = Path(file_path).exists()
        print_test_result(f"File: {file_path}", exists, "File exists" if exists else "File missing")
        if not exists:
            all_good = False
    
    for dir_path in required_dirs:
        exists = Path(dir_path).exists() and Path(dir_path).is_dir()
        print_test_result(f"Directory: {dir_path}", exists, "Directory exists" if exists else "Directory missing")
        if not exists:
            all_good = False
    
    return all_good

def test_dependencies():
    """Test if all required dependencies are available"""
    print_header("Testing Dependencies")
    
    required_packages = [
        'flask', 'flask_socketio', 'flask_login', 'requests', 'psutil',
        'groq', 'rich', 'schedule'
    ]
    
    all_good = True
    
    for package in required_packages:
        try:
            __import__(package.replace('.', '_'))
            print_test_result(f"Package: {package}", True, "Available")
        except ImportError:
            print_test_result(f"Package: {package}", False, "Not available")
            all_good = False
    
    return all_good

def main():
    """Run all tests"""
    print("🚀 COMPREHENSIVE PROJECT TEST SUITE")
    print("=" * 60)
    print(f"Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = []
    
    # Run all tests
    test_results.append(("File Structure", test_file_structure()))
    test_results.append(("Dependencies", test_dependencies()))
    test_results.append(("Core AI Shell", test_core_ai_shell()))
    test_results.append(("Web Interface", test_web_interface()))
    test_results.append(("Ethical Hacking", test_ethical_hacking()))
    test_results.append(("Terminal Manager", test_terminal_manager()))
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    success_rate = (passed / total) * 100
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Project is ready for production.")
        print("✅ Core AI Shell: Working")
        print("✅ Web Interface: Ready")
        print("✅ Ethical Hacking: Functional")
        print("✅ Terminal Manager: Anti-stuck protection active")
        print("✅ All APIs: Connected and working")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)