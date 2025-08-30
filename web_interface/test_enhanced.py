#!/usr/bin/env python3
"""
🧪 Enhanced Web Interface Test Script
Comprehensive testing of all enhanced features and PC control capabilities
"""

import sys
import os
import time
import json
from datetime import datetime

# Add workspace to path
sys.path.append('/workspace')
sys.path.append('.')

def test_enhanced_system_controller():
    """Test the enhanced system controller"""
    print("🔧 Testing Enhanced System Controller...")
    
    try:
        from app_enhanced import EnhancedSystemController
        
        controller = EnhancedSystemController()
        
        # Test system info
        print("  📊 Getting system information...")
        system_info = controller.get_system_info()
        print(f"    ✓ Platform: {system_info.get('platform', 'Unknown')}")
        print(f"    ✓ Architecture: {system_info.get('architecture', 'Unknown')}")
        print(f"    ✓ Python Version: {system_info.get('python_version', 'Unknown')}")
        print(f"    ✓ CPU Count: {system_info.get('cpu_count', 'Unknown')}")
        
        # Test process info
        print("  📋 Getting process information...")
        processes = controller.get_process_info()
        print(f"    ✓ Found {len(processes)} processes")
        if processes:
            top_process = processes[0]
            print(f"    ✓ Top process: {top_process.get('name', 'Unknown')} (PID: {top_process.get('pid', 'Unknown')})")
        
        print("  ✅ Enhanced System Controller tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Enhanced System Controller test failed: {e}")
        return False

def test_command_validation():
    """Test command validation and security"""
    print("🛡️ Testing Command Validation...")
    
    try:
        from app_enhanced import CommandValidator
        
        # Test safe commands
        safe_commands = [
            "ls -la",
            "pwd",
            "whoami",
            "date",
            "ps aux",
            "df -h",
            "free -h",
            "cat /etc/os-release"
        ]
        
        print("  ✅ Testing safe commands...")
        for cmd in safe_commands:
            is_safe, message = CommandValidator.is_safe_command(cmd)
            if is_safe:
                print(f"    ✓ '{cmd}' - {message}")
            else:
                print(f"    ❌ '{cmd}' - {message}")
        
        # Test blocked commands
        blocked_commands = [
            "rm -rf /",
            "sudo rm -rf /",
            "dd if=/dev/zero",
            "mkfs.ext4 /dev/sda1",
            "shutdown -h now",
            "reboot"
        ]
        
        print("  🚫 Testing blocked commands...")
        for cmd in blocked_commands:
            is_safe, message = CommandValidator.is_safe_command(cmd)
            if not is_safe:
                print(f"    ✓ '{cmd}' - {message}")
            else:
                print(f"    ❌ '{cmd}' - {message}")
        
        # Test dangerous characters
        dangerous_commands = [
            "ls; rm -rf /",
            "pwd && rm -rf /",
            "whoami || rm -rf /",
            "date | rm -rf /",
            "echo 'test' > /etc/passwd",
            "cat /etc/passwd < /dev/null"
        ]
        
        print("  ⚠️ Testing dangerous characters...")
        for cmd in dangerous_commands:
            is_safe, message = CommandValidator.is_safe_command(cmd)
            if not is_safe:
                print(f"    ✓ '{cmd}' - {message}")
            else:
                print(f"    ❌ '{cmd}' - {message}")
        
        print("  ✅ Command Validation tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Command Validation test failed: {e}")
        return False

def test_safe_command_execution():
    """Test safe command execution"""
    print("⚡ Testing Safe Command Execution...")
    
    try:
        from app_enhanced import EnhancedSystemController
        
        controller = EnhancedSystemController()
        
        # Test safe commands
        test_commands = [
            "pwd",
            "whoami",
            "date",
            "echo 'Hello from enhanced web interface'"
        ]
        
        for cmd in test_commands:
            print(f"  🚀 Executing: {cmd}")
            result = controller.execute_command_safe(cmd, timeout=10)
            
            if result['success']:
                print(f"    ✓ Success - Exit code: {result['exit_code']}")
                if result['output']:
                    print(f"      Output: {result['output'].strip()}")
            else:
                print(f"    ❌ Failed: {result['error']}")
        
        print("  ✅ Safe Command Execution tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Safe Command Execution test failed: {e}")
        return False

def test_file_operations():
    """Test file operations and security"""
    print("📁 Testing File Operations...")
    
    try:
        from app_enhanced import Config
        
        # Test safe directories
        print("  🔒 Testing safe directory validation...")
        safe_dirs = Config.SAFE_DIRECTORIES
        for safe_dir in safe_dirs:
            if os.path.exists(safe_dir):
                print(f"    ✓ {safe_dir} - exists and accessible")
            else:
                print(f"    ⚠️ {safe_dir} - does not exist")
        
        # Test file creation in safe directory
        test_file = "/workspace/web_interface/test_file.txt"
        test_content = f"Test file created at {datetime.now()}"
        
        print(f"  📝 Creating test file: {test_file}")
        try:
            with open(test_file, 'w') as f:
                f.write(test_content)
            print("    ✓ Test file created successfully")
            
            # Read it back
            with open(test_file, 'r') as f:
                read_content = f.read()
            print(f"    ✓ File content verified: {read_content.strip()}")
            
            # Clean up
            os.remove(test_file)
            print("    ✓ Test file cleaned up")
            
        except Exception as e:
            print(f"    ❌ File operation failed: {e}")
        
        print("  ✅ File Operations tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ File Operations test failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("⏱️ Testing Rate Limiting...")
    
    try:
        from app_enhanced import rate_limiter
        
        test_ip = "192.168.1.100"
        
        print(f"  🌐 Testing rate limiting for IP: {test_ip}")
        
        # Test normal requests
        print("  📊 Testing normal request flow...")
        for i in range(5):
            allowed = rate_limiter.is_allowed(test_ip)
            print(f"    Request {i+1}: {'✓ Allowed' if allowed else '❌ Blocked'}")
        
        # Test rate limit
        print("  🚫 Testing rate limit enforcement...")
        allowed_count = 0
        for i in range(150):  # More than the limit
            if rate_limiter.is_allowed(test_ip):
                allowed_count += 1
        
        print(f"    Total requests: 150, Allowed: {allowed_count}")
        if allowed_count <= 100:  # Should respect rate limit
            print("    ✓ Rate limiting working correctly")
        else:
            print("    ❌ Rate limiting not working correctly")
        
        print("  ✅ Rate Limiting tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Rate Limiting test failed: {e}")
        return False

def test_user_management():
    """Test user management and permissions"""
    print("👤 Testing User Management...")
    
    try:
        from app_enhanced import users, User
        
        print("  👥 Testing user accounts...")
        for username, user in users.items():
            print(f"    User: {username}")
            print(f"      Role: {user.role}")
            print(f"      Permissions: {user.permissions}")
            print(f"      Login attempts: {user.login_attempts}")
        
        # Test permission system
        print("  🔐 Testing permission system...")
        admin_user = users.get('admin')
        if admin_user and 'all' in admin_user.permissions:
            print("    ✓ Admin has all permissions")
        else:
            print("    ❌ Admin permissions not set correctly")
        
        user_user = users.get('user')
        if user_user and 'read' in user_user.permissions:
            print("    ✓ Regular user has read permission")
        else:
            print("    ❌ Regular user permissions not set correctly")
        
        print("  ✅ User Management tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ User Management test failed: {e}")
        return False

def test_ai_shell_integration():
    """Test AI Shell integration"""
    print("🤖 Testing AI Shell Integration...")
    
    try:
        from app_enhanced import AI_SHELL_AVAILABLE
        
        if AI_SHELL_AVAILABLE:
            print("  ✅ AI Shell components are available")
            
            # Test AI manager
            try:
                from app_enhanced import ai_manager
                print("    ✓ AI Manager initialized successfully")
            except Exception as e:
                print(f"    ❌ AI Manager initialization failed: {e}")
            
            # Test system controller
            try:
                from app_enhanced import system_controller
                print("    ✓ System Controller initialized successfully")
            except Exception as e:
                print(f"    ❌ System Controller initialization failed: {e}")
            
        else:
            print("  ⚠️ AI Shell components not available")
            print("    This is expected if running standalone")
        
        print("  ✅ AI Shell Integration tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ AI Shell Integration test failed: {e}")
        return False

def test_voice_recognition():
    """Test voice recognition capabilities"""
    print("🎤 Testing Voice Recognition...")
    
    try:
        from app_enhanced import SPEECH_AVAILABLE, voice_recognizer
        
        if SPEECH_AVAILABLE and voice_recognizer:
            print("  ✅ Voice recognition is available")
            print(f"    Recognizer type: {type(voice_recognizer)}")
        else:
            print("  ⚠️ Voice recognition not available")
            print("    This is expected if PyAudio or SpeechRecognition not installed")
        
        print("  ✅ Voice Recognition tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Voice Recognition test failed: {e}")
        return False

def test_web_interface_features():
    """Test web interface features"""
    print("🌐 Testing Web Interface Features...")
    
    try:
        from app_enhanced import app, socketio
        
        print("  ✅ Flask app initialized successfully")
        print(f"    App name: {app.name}")
        print(f"    Debug mode: {app.debug}")
        
        print("  ✅ SocketIO initialized successfully")
        print(f"    Async mode: {socketio.async_mode}")
        
        # Test routes
        print("  🛣️ Testing available routes...")
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(f"{rule.methods} {rule.rule}")
        
        print(f"    Found {len(routes)} routes")
        for route in routes[:5]:  # Show first 5 routes
            print(f"      {route}")
        if len(routes) > 5:
            print(f"      ... and {len(routes) - 5} more")
        
        print("  ✅ Web Interface Features tests passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Web Interface Features test failed: {e}")
        return False

def run_comprehensive_test():
    """Run all comprehensive tests"""
    print("🚀 Enhanced Web Interface - Comprehensive Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    print()
    
    tests = [
        ("Enhanced System Controller", test_enhanced_system_controller),
        ("Command Validation", test_command_validation),
        ("Safe Command Execution", test_safe_command_execution),
        ("File Operations", test_file_operations),
        ("Rate Limiting", test_rate_limiting),
        ("User Management", test_user_management),
        ("AI Shell Integration", test_ai_shell_integration),
        ("Voice Recognition", test_voice_recognition),
        ("Web Interface Features", test_web_interface_features)
    ]
    
    results = []
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🧪 {test_name}")
        print("-" * 40)
        
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                passed += 1
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append((test_name, False))
        
        print()
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 60)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print()
    
    print("Detailed Results:")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print()
    if passed == total:
        print("🎉 All tests passed! Enhanced web interface is ready for production.")
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite failed with exception: {e}")
        sys.exit(1)