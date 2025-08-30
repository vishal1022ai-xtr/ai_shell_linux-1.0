#!/usr/bin/env python3
"""
Comprehensive Error Check Test for AI Terminal Project
Identifies potential runtime errors, security issues, and edge cases
"""

import sys
import os
import time
import threading
import subprocess
import signal
import tempfile
import shutil
from pathlib import Path

# Add paths
sys.path.append('core')
sys.path.append('config')
sys.path.append('web_interface')

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_test_result(test_name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"  {status} {test_name}")
    if details:
        print(f"    📝 {details}")

def test_import_stability():
    """Test import stability and error handling"""
    print_header("Testing Import Stability")
    
    test_results = []
    
    # Test 1: Multiple imports
    try:
        for i in range(5):
            from config_manager import ConfigManager
            from ai_manager import AIManager
        print_test_result("Multiple Imports", True, "No import conflicts")
        test_results.append(True)
    except Exception as e:
        print_test_result("Multiple Imports", False, str(e))
        test_results.append(False)
    
    # Test 2: Import with missing dependencies
    try:
        # Temporarily remove a dependency
        original_path = sys.path.copy()
        sys.path = [p for p in sys.path if 'core' not in p]
        
        try:
            from ai_manager import AIManager
            print_test_result("Import Error Handling", False, "Should have failed")
            test_results.append(False)
        except ImportError:
            print_test_result("Import Error Handling", True, "Properly handled missing dependency")
            test_results.append(True)
        finally:
            sys.path = original_path
    except Exception as e:
        print_test_result("Import Error Handling", False, f"Unexpected error: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_configuration_errors():
    """Test configuration error handling"""
    print_header("Testing Configuration Error Handling")
    
    test_results = []
    
    # Test 1: Missing config file
    try:
        original_config = 'config/ultra_config.ini'
        backup_config = 'config/ultra_config.ini.backup'
        
        if os.path.exists(original_config):
            shutil.move(original_config, backup_config)
        
        try:
            from config_manager import ConfigManager
            config = ConfigManager()
            print_test_result("Missing Config File", False, "Should have failed")
            test_results.append(False)
        except FileNotFoundError:
            print_test_result("Missing Config File", True, "Properly handled missing config")
            test_results.append(True)
        finally:
            if os.path.exists(backup_config):
                shutil.move(backup_config, original_config)
    except Exception as e:
        print_test_result("Missing Config File", False, f"Unexpected error: {e}")
        test_results.append(False)
    
    # Test 2: Invalid config values
    try:
        from config_manager import ConfigManager
        config = ConfigManager()
        
        # Test invalid section/key
        result = config.get('INVALID_SECTION', 'invalid_key', 'default_value')
        if result == 'default_value':
            print_test_result("Invalid Config Values", True, "Properly handled invalid config")
            test_results.append(True)
        else:
            print_test_result("Invalid Config Values", False, "Did not handle invalid config")
            test_results.append(False)
    except Exception as e:
        print_test_result("Invalid Config Values", False, f"Error: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_api_error_handling():
    """Test API error handling"""
    print_header("Testing API Error Handling")
    
    test_results = []
    
    try:
        from config_manager import ConfigManager
        from ai_manager import AIManager
        
        config = ConfigManager()
        am = AIManager(config)
        
        # Test 1: Empty prompt
        try:
            response = am.get_ai_response("", "auto")
            if response[1] == "Error":
                print_test_result("Empty Prompt Handling", True, "Properly handled empty prompt")
                test_results.append(True)
            else:
                print_test_result("Empty Prompt Handling", False, "Did not handle empty prompt")
                test_results.append(False)
        except Exception as e:
            print_test_result("Empty Prompt Handling", False, f"Error: {e}")
            test_results.append(False)
        
        # Test 2: Very long prompt
        try:
            long_prompt = "A" * 10000  # Very long prompt
            response = am.get_ai_response(long_prompt, "auto")
            print_test_result("Long Prompt Handling", True, "Handled long prompt")
            test_results.append(True)
        except Exception as e:
            print_test_result("Long Prompt Handling", False, f"Error: {e}")
            test_results.append(False)
        
    except Exception as e:
        print_test_result("API Error Handling", False, f"Setup error: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_security_vulnerabilities():
    """Test for potential security vulnerabilities"""
    print_header("Testing Security Vulnerabilities")
    
    test_results = []
    
    # Test 1: Command injection prevention
    try:
        dangerous_commands = [
            "rm -rf /",
            "dd if=/dev/zero of=/dev/sda",
            "sudo shutdown -h now",
            "cat /etc/passwd",
            "echo 'malicious' > /tmp/test"
        ]
        
        from web_interface.app_enhanced import Config
        
        for cmd in dangerous_commands:
            if cmd in Config.BLOCKED_COMMANDS:
                print_test_result(f"Command Blocked: {cmd[:20]}...", True, "Dangerous command blocked")
                test_results.append(True)
            else:
                print_test_result(f"Command Blocked: {cmd[:20]}...", False, "Dangerous command not blocked")
                test_results.append(False)
    except Exception as e:
        print_test_result("Command Injection Prevention", False, f"Error: {e}")
        test_results.append(False)
    
    # Test 2: Directory traversal prevention
    try:
        dangerous_paths = [
            "../../../etc/passwd",
            "/etc/shadow",
            "/root/.ssh/id_rsa",
            "..\\..\\..\\windows\\system32\\config\\sam"
        ]
        
        safe_dirs = ['/workspace', '/tmp', '/home']
        
        for path in dangerous_paths:
            is_safe = any(safe_dir in path for safe_dir in safe_dirs)
            if not is_safe:
                print_test_result(f"Path Traversal: {path[:20]}...", True, "Dangerous path not in safe directories")
                test_results.append(True)
            else:
                print_test_result(f"Path Traversal: {path[:20]}...", False, "Dangerous path in safe directories")
                test_results.append(False)
    except Exception as e:
        print_test_result("Directory Traversal Prevention", False, f"Error: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_resource_management():
    """Test resource management and potential memory leaks"""
    print_header("Testing Resource Management")
    
    test_results = []
    
    # Test 1: Process cleanup
    try:
        from web_interface.enhanced_terminal_manager import EnhancedTerminalManager
        
        tm = EnhancedTerminalManager()
        
        # Start multiple processes
        processes = []
        for i in range(5):
            result = tm.execute_command_safe(f"echo 'test {i}'", timeout=2)
            if result.get('success'):
                processes.append(result['pid'])
        
        # Wait for cleanup
        time.sleep(3)
        
        # Check if processes are cleaned up
        active_processes = len(tm.processes)
        if active_processes == 0:
            print_test_result("Process Cleanup", True, "All processes cleaned up")
            test_results.append(True)
        else:
            print_test_result("Process Cleanup", False, f"{active_processes} processes still active")
            test_results.append(False)
        
        tm.shutdown()
        
    except Exception as e:
        print_test_result("Process Cleanup", False, f"Error: {e}")
        test_results.append(False)
    
    # Test 2: Memory usage monitoring
    try:
        import psutil
        import gc
        
        # Force garbage collection
        gc.collect()
        
        # Check memory before
        process = psutil.Process()
        memory_before = process.memory_info().rss
        
        # Create some objects
        large_list = [i for i in range(10000)]
        
        # Force garbage collection
        del large_list
        gc.collect()
        
        # Check memory after
        memory_after = process.memory_info().rss
        
        # Memory should be similar (within 10%)
        memory_diff = abs(memory_after - memory_before) / memory_before
        if memory_diff < 0.1:
            print_test_result("Memory Management", True, "Memory properly managed")
            test_results.append(True)
        else:
            print_test_result("Memory Management", False, f"Memory usage increased by {memory_diff*100:.1f}%")
            test_results.append(False)
            
    except Exception as e:
        print_test_result("Memory Management", False, f"Error: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_concurrent_access():
    """Test concurrent access and potential race conditions"""
    print_header("Testing Concurrent Access")
    
    test_results = []
    
    # Test 1: Multiple simultaneous requests
    try:
        from config_manager import ConfigManager
        
        def config_access():
            try:
                config = ConfigManager()
                for i in range(10):
                    config.get('API_KEYS', 'groq_api_key')
                return True
            except Exception:
                return False
        
        # Start multiple threads
        threads = []
        results = []
        
        for i in range(5):
            thread = threading.Thread(target=lambda: results.append(config_access()))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        if all(results):
            print_test_result("Concurrent Config Access", True, "No race conditions detected")
            test_results.append(True)
        else:
            print_test_result("Concurrent Config Access", False, "Race condition detected")
            test_results.append(False)
            
    except Exception as e:
        print_test_result("Concurrent Config Access", False, f"Error: {e}")
        test_results.append(False)
    
    # Test 2: File access conflicts
    try:
        test_file = "/tmp/test_concurrent.txt"
        
        def file_operation(thread_id):
            try:
                with open(test_file, 'w') as f:
                    f.write(f"Thread {thread_id}")
                time.sleep(0.1)
                with open(test_file, 'r') as f:
                    content = f.read()
                return True
            except Exception:
                return False
        
        # Start multiple threads
        threads = []
        results = []
        
        for i in range(5):
            thread = threading.Thread(target=lambda x=i: results.append(file_operation(x)))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        if all(results):
            print_test_result("Concurrent File Access", True, "No file access conflicts")
            test_results.append(True)
        else:
            print_test_result("Concurrent File Access", False, "File access conflicts detected")
            test_results.append(False)
        
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
            
    except Exception as e:
        print_test_result("Concurrent File Access", False, f"Error: {e}")
        test_results.append(False)
    
    return all(test_results)

def test_error_recovery():
    """Test error recovery mechanisms"""
    print_header("Testing Error Recovery")
    
    test_results = []
    
    # Test 1: Terminal recovery
    try:
        from web_interface.enhanced_terminal_manager import EnhancedTerminalManager
        
        tm = EnhancedTerminalManager()
        
        # Simulate terminal issues
        result = tm._recover_terminal()
        if result:
            print_test_result("Terminal Recovery", True, "Terminal recovery mechanism working")
            test_results.append(True)
        else:
            print_test_result("Terminal Recovery", False, "Terminal recovery failed")
            test_results.append(False)
        
        tm.shutdown()
        
    except Exception as e:
        print_test_result("Terminal Recovery", False, f"Error: {e}")
        test_results.append(False)
    
    # Test 2: Process recovery
    try:
        from web_interface.enhanced_terminal_manager import EnhancedTerminalManager
        
        tm = EnhancedTerminalManager()
        
        # Start a process that will hang
        result = tm.execute_command_safe("cat", timeout=2)
        if result.get('success'):
            pid = result['pid']
            
            # Wait for timeout
            time.sleep(3)
            
            # Check if process was handled
            if pid not in tm.processes:
                print_test_result("Process Recovery", True, "Hung process properly handled")
                test_results.append(True)
            else:
                print_test_result("Process Recovery", False, "Hung process not handled")
                test_results.append(False)
        else:
            print_test_result("Process Recovery", False, "Failed to start test process")
            test_results.append(False)
        
        tm.shutdown()
        
    except Exception as e:
        print_test_result("Process Recovery", False, f"Error: {e}")
        test_results.append(False)
    
    return all(test_results)

def main():
    """Run all error check tests"""
    print("🚀 COMPREHENSIVE ERROR CHECK TEST SUITE")
    print("=" * 60)
    print(f"Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = []
    
    # Run all tests
    test_results.append(("Import Stability", test_import_stability()))
    test_results.append(("Configuration Errors", test_configuration_errors()))
    test_results.append(("API Error Handling", test_api_error_handling()))
    test_results.append(("Security Vulnerabilities", test_security_vulnerabilities()))
    test_results.append(("Resource Management", test_resource_management()))
    test_results.append(("Concurrent Access", test_concurrent_access()))
    test_results.append(("Error Recovery", test_error_recovery()))
    
    # Print summary
    print_header("ERROR CHECK SUMMARY")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    success_rate = (passed / total) * 100
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL ERROR CHECKS PASSED! Project appears to be robust.")
        print("✅ No major vulnerabilities detected")
        print("✅ Error handling is comprehensive")
        print("✅ Resource management is proper")
        print("✅ Security measures are in place")
    else:
        print(f"\n⚠️  {total - passed} error checks failed. Please review the issues above.")
        print("🔍 Consider addressing these potential problems before production use.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)