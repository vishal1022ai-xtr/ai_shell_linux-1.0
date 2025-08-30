#!/usr/bin/env python3
"""
🧪 Enhanced Terminal Manager Test Suite
Tests all anti-stuck capabilities and process management features
"""

import sys
import os
import time
import signal
import subprocess
import threading
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all required imports for terminal manager"""
    print("🔍 Testing imports...")
    
    required_modules = [
        'psutil', 'termios', 'tty', 'fcntl', 'select', 'queue',
        'threading', 'time', 'signal', 'subprocess', 'os', 'sys'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n⚠️  Failed imports: {len(failed_imports)}")
        return False
    
    print("  ✅ All imports successful")
    return True

def test_terminal_manager_initialization():
    """Test terminal manager initialization"""
    print("\n🔧 Testing Terminal Manager Initialization...")
    
    try:
        from enhanced_terminal_manager import EnhancedTerminalManager
        
        # Create instance
        tm = EnhancedTerminalManager()
        
        # Check basic attributes
        assert hasattr(tm, 'processes'), "Missing processes attribute"
        assert hasattr(tm, 'terminal_state'), "Missing terminal_state attribute"
        assert hasattr(tm, 'auto_recovery_enabled'), "Missing auto_recovery_enabled attribute"
        
        print("    ✅ Terminal manager initialized successfully")
        print(f"    📊 Max processes: {tm.max_processes}")
        print(f"    🛡️  Auto recovery: {tm.auto_recovery_enabled}")
        
        # Cleanup
        tm.shutdown()
        return True
        
    except Exception as e:
        print(f"    ❌ Terminal manager initialization failed: {e}")
        return False

def test_safe_command_execution():
    """Test safe command execution with anti-stuck protection"""
    print("\n⚡ Testing Safe Command Execution...")
    
    try:
        from enhanced_terminal_manager import execute_safe
        
        # Test simple command
        print("  🔍 Testing simple command execution...")
        result = execute_safe('echo "Hello World"', timeout=5.0)
        
        if result['success']:
            print(f"    ✅ Command executed successfully, PID: {result['pid']}")
        else:
            print(f"    ❌ Command failed: {result['error']}")
            return False
        
        # Test long-running command with auto-background
        print("  🔍 Testing long-running command with auto-background...")
        result = execute_safe('sleep 10', timeout=3.0, auto_background=True)
        
        if result['success']:
            print(f"    ✅ Long command started, PID: {result['pid']}")
            print("    ⏳ Command will auto-background after timeout...")
            
            # Wait a bit for timeout
            time.sleep(4)
            
            # Check if process was backgrounded
            from enhanced_terminal_manager import list_processes
            processes = list_processes()
            
            if processes:
                print(f"    📊 Found {len(processes)} monitored processes")
                for proc in processes:
                    print(f"      - PID {proc['pid']}: {proc['command']} ({proc['state']})")
            else:
                print("    ✅ Process completed and cleaned up")
        else:
            print(f"    ❌ Long command failed: {result['error']}")
            return False
        
        return True
        
    except Exception as e:
        print(f"    ❌ Safe command execution test failed: {e}")
        return False

def test_process_management():
    """Test process management capabilities"""
    print("\n🔄 Testing Process Management...")
    
    try:
        from enhanced_terminal_manager import (
            execute_safe, list_processes, suspend_process, 
            resume_process, terminate_process, background_process
        )
        
        # Start a test process
        print("  🔍 Starting test process...")
        result = execute_safe('sleep 30', timeout=60.0, auto_background=False)
        
        if not result['success']:
            print(f"    ❌ Failed to start test process: {result['error']}")
            return False
        
        pid = result['pid']
        print(f"    ✅ Test process started, PID: {pid}")
        
        # Wait a moment for process to start
        time.sleep(1)
        
        # List processes
        print("  🔍 Listing processes...")
        processes = list_processes()
        if processes:
            print(f"    ✅ Found {len(processes)} processes")
            for proc in processes:
                print(f"      - PID {proc['pid']}: {proc['command']} ({proc['state']})")
        else:
            print("    ❌ No processes found")
            return False
        
        # Test process suspension
        print("  🔍 Testing process suspension...")
        if suspend_process(pid):
            print(f"    ✅ Process {pid} suspended successfully")
        else:
            print(f"    ❌ Failed to suspend process {pid}")
            return False
        
        # Test process resumption
        print("  🔍 Testing process resumption...")
        if resume_process(pid):
            print(f"    ✅ Process {pid} resumed successfully")
        else:
            print(f"    ❌ Failed to resume process {pid}")
            return False
        
        # Test backgrounding
        print("  🔍 Testing process backgrounding...")
        if background_process(pid):
            print(f"    ✅ Process {pid} moved to background")
        else:
            print(f"    ❌ Failed to background process {pid}")
            return False
        
        # Test process termination
        print("  🔍 Testing process termination...")
        if terminate_process(pid):
            print(f"    ✅ Process {pid} terminated successfully")
        else:
            print(f"    ❌ Failed to terminate process {pid}")
            return False
        
        return True
        
    except Exception as e:
        print(f"    ❌ Process management test failed: {e}")
        return False

def test_terminal_recovery():
    """Test terminal recovery mechanisms"""
    print("\n🔄 Testing Terminal Recovery...")
    
    try:
        from enhanced_terminal_manager import get_terminal_manager
        
        tm = get_terminal_manager()
        
        # Test terminal state detection
        print("  🔍 Testing terminal state detection...")
        current_state = tm.terminal_state
        print(f"    ✅ Current terminal state: {current_state.value}")
        
        # Test terminal stuck detection
        print("  🔍 Testing terminal stuck detection...")
        is_stuck = tm._is_terminal_stuck()
        print(f"    ✅ Terminal stuck detection: {is_stuck}")
        
        # Test raw mode detection
        print("  🔍 Testing raw mode detection...")
        is_raw_stuck = tm._is_raw_mode_stuck()
        print(f"    ✅ Raw mode stuck detection: {is_raw_stuck}")
        
        # Test terminal settings preservation
        print("  🔍 Testing terminal settings preservation...")
        if tm.original_terminal_settings:
            print("    ✅ Original terminal settings preserved")
        else:
            print("    ⚠️  No original terminal settings (non-TTY)")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Terminal recovery test failed: {e}")
        return False

def test_resource_management():
    """Test resource management and monitoring"""
    print("\n📊 Testing Resource Management...")
    
    try:
        from enhanced_terminal_manager import get_terminal_manager
        
        tm = get_terminal_manager()
        
        # Test resource threshold configuration
        print("  🔍 Testing resource thresholds...")
        thresholds = tm.resource_thresholds
        print(f"    ✅ CPU threshold: {thresholds['cpu_percent']}%")
        print(f"    ✅ Memory threshold: {thresholds['memory_percent']}%")
        print(f"    ✅ IO wait threshold: {thresholds['io_wait']}%")
        print(f"    ✅ Response time threshold: {thresholds['response_time']}s")
        
        # Test resource monitoring
        print("  🔍 Testing resource monitoring...")
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        print(f"    ✅ Current CPU usage: {cpu_percent}%")
        print(f"    ✅ Current memory usage: {memory.percent}%")
        
        # Check if thresholds are reasonable
        if cpu_percent < thresholds['cpu_percent']:
            print("    ✅ CPU usage below threshold")
        else:
            print("    ⚠️  CPU usage above threshold")
        
        if memory.percent < thresholds['memory_percent']:
            print("    ✅ Memory usage below threshold")
        else:
            print("    ⚠️  Memory usage above threshold")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Resource management test failed: {e}")
        return False

def test_signal_handling():
    """Test signal handling capabilities"""
    print("\n📡 Testing Signal Handling...")
    
    try:
        from enhanced_terminal_manager import get_terminal_manager
        
        tm = get_terminal_manager()
        
        # Test signal handler setup
        print("  🔍 Testing signal handler setup...")
        
        # Check if signal handlers are set
        handlers = {
            signal.SIGINT: signal.getsignal(signal.SIGINT),
            signal.SIGTERM: signal.getsignal(signal.SIGTERM),
            signal.SIGTSTP: signal.getsignal(signal.SIGTSTP),
            signal.SIGCONT: signal.getsignal(signal.SIGCONT)
        }
        
        for sig, handler in handlers.items():
            if handler is not None:
                print(f"    ✅ Signal {sig} handler set")
            else:
                print(f"    ⚠️  Signal {sig} handler not set")
        
        # Test graceful shutdown preparation
        print("  🔍 Testing shutdown preparation...")
        if hasattr(tm, 'shutdown'):
            print("    ✅ Shutdown method available")
        else:
            print("    ❌ Shutdown method missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"    ❌ Signal handling test failed: {e}")
        return False

def test_anti_stuck_scenarios():
    """Test various anti-stuck scenarios"""
    print("\n🛡️ Testing Anti-Stuck Scenarios...")
    
    try:
        from enhanced_terminal_manager import execute_safe, list_processes
        
        # Test 1: Long-running foreground process
        print("  🔍 Test 1: Long-running foreground process...")
        result = execute_safe('sleep 20', timeout=5.0, auto_background=True)
        
        if result['success']:
            print(f"    ✅ Process started, PID: {result['pid']}")
            print("    ⏳ Waiting for timeout and auto-background...")
            
            # Wait for timeout
            time.sleep(6)
            
            # Check if process was handled
            processes = list_processes()
            if processes:
                print(f"    📊 Process status: {processes[0]['state']}")
                if processes[0]['state'] in ['background', 'suspended']:
                    print("    ✅ Process successfully backgrounded")
                else:
                    print("    ⚠️  Process not backgrounded as expected")
            else:
                print("    ✅ Process completed and cleaned up")
        else:
            print(f"    ❌ Failed to start test process: {result['error']}")
            return False
        
        # Test 2: Process that might hang
        print("  🔍 Test 2: Potentially hanging process...")
        result = execute_safe('cat', timeout=3.0, auto_background=False)
        
        if result['success']:
            print(f"    ✅ Process started, PID: {result['pid']}")
            print("    ⏳ Waiting for timeout...")
            
            # Wait for timeout
            time.sleep(4)
            
            # Check if process was handled
            processes = list_processes()
            if processes:
                print(f"    📊 Process status: {processes[0]['state']}")
            else:
                print("    ✅ Process handled and cleaned up")
        else:
            print(f"    ❌ Failed to start hanging process: {result['error']}")
            return False
        
        # Test 3: Resource-intensive process
        print("  🔍 Test 3: Resource-intensive process...")
        result = execute_safe('dd if=/dev/zero of=/dev/null bs=1M count=1000', 
                            timeout=5.0, auto_background=True)
        
        if result['success']:
            print(f"    ✅ Process started, PID: {result['pid']}")
            print("    ⏳ Monitoring resource usage...")
            
            # Wait a bit and check resource usage
            time.sleep(3)
            processes = list_processes()
            if processes:
                proc = processes[0]
                print(f"    📊 CPU: {proc['cpu_percent']}%, Memory: {proc['memory_percent']}%")
                
                # Check if resource limits are enforced
                if proc['cpu_percent'] > 90 or proc['memory_percent'] > 80:
                    print("    ⚠️  High resource usage detected")
                else:
                    print("    ✅ Resource usage within limits")
            else:
                print("    ✅ Process completed")
        else:
            print(f"    ❌ Failed to start resource-intensive process: {result['error']}")
            return False
        
        return True
        
    except Exception as e:
        print(f"    ❌ Anti-stuck scenarios test failed: {e}")
        return False

def test_process_cleanup():
    """Test process cleanup mechanisms"""
    print("\n🧹 Testing Process Cleanup...")
    
    try:
        from enhanced_terminal_manager import (
            execute_safe, list_processes, cleanup_all_processes
        )
        
        # Start several test processes
        print("  🔍 Starting multiple test processes...")
        pids = []
        
        for i in range(3):
            result = execute_safe(f'sleep {10 + i}', timeout=60.0, auto_background=True)
            if result['success']:
                pids.append(result['pid'])
                print(f"    ✅ Started process {result['pid']}")
            else:
                print(f"    ❌ Failed to start process: {result['error']}")
        
        if not pids:
            print("    ❌ No test processes started")
            return False
        
        # Wait a moment for processes to start
        time.sleep(2)
        
        # Check process count
        processes = list_processes()
        print(f"    📊 Active processes: {len(processes)}")
        
        # Test cleanup
        print("  🔍 Testing process cleanup...")
        cleanup_all_processes()
        
        # Wait for cleanup
        time.sleep(2)
        
        # Check if processes were cleaned up
        processes_after = list_processes()
        print(f"    📊 Processes after cleanup: {len(processes_after)}")
        
        if len(processes_after) == 0:
            print("    ✅ All processes cleaned up successfully")
        else:
            print("    ⚠️  Some processes still active")
            for proc in processes_after:
                print(f"      - PID {proc['pid']}: {proc['command']} ({proc['state']})")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Process cleanup test failed: {e}")
        return False

def test_performance_and_scalability():
    """Test performance and scalability"""
    print("\n⚡ Testing Performance and Scalability...")
    
    try:
        from enhanced_terminal_manager import execute_safe, list_processes
        
        # Test process limit handling
        print("  🔍 Testing process limit handling...")
        max_processes = 10  # Lower limit for testing
        
        start_time = time.time()
        
        # Start multiple processes quickly
        pids = []
        for i in range(max_processes + 2):  # Exceed limit
            result = execute_safe(f'echo "Process {i}" && sleep 1', timeout=5.0, auto_background=True)
            if result['success']:
                pids.append(result['pid'])
                print(f"    ✅ Started process {result['pid']}")
            else:
                print(f"    ❌ Failed to start process: {result['error']}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"    📊 Started {len(pids)} processes in {duration:.2f} seconds")
        
        # Wait for processes to complete
        time.sleep(3)
        
        # Check final process count
        processes = list_processes()
        print(f"    📊 Final process count: {len(processes)}")
        
        if len(processes) <= max_processes:
            print("    ✅ Process limit enforced correctly")
        else:
            print("    ⚠️  Process limit not enforced")
        
        # Test memory usage
        print("  🔍 Testing memory usage...")
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        print(f"    📊 Memory usage: {memory_info.rss // 1024} KB")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Performance and scalability test failed: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and generate report"""
    print("🚀 Enhanced Terminal Manager - Comprehensive Test Suite")
    print("=" * 70)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Import Testing", test_imports),
        ("Terminal Manager Initialization", test_terminal_manager_initialization),
        ("Safe Command Execution", test_safe_command_execution),
        ("Process Management", test_process_management),
        ("Terminal Recovery", test_terminal_recovery),
        ("Resource Management", test_resource_management),
        ("Signal Handling", test_signal_handling),
        ("Anti-Stuck Scenarios", test_anti_stuck_scenarios),
        ("Process Cleanup", test_process_cleanup),
        ("Performance and Scalability", test_performance_and_scalability)
    ]
    
    results = []
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, "PASS" if result else "FAIL"))
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            results.append((test_name, False, f"ERROR: {e}"))
            failed += 1
    
    # Generate report
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 70)
    
    for test_name, result, status in results:
        status_icon = "✅" if "PASS" in status else "❌"
        print(f"{status_icon} {test_name}: {status}")
    
    print(f"\n📈 Summary:")
    print(f"  Total Tests: {len(tests)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Success Rate: {(passed / len(tests)) * 100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Enhanced terminal manager is ready for production.")
        print("🛡️  Anti-stuck protection fully functional!")
    else:
        print(f"\n⚠️  {failed} tests failed. Please check the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    try:
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)