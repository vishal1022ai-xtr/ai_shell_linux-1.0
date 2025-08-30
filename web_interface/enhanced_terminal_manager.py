#!/usr/bin/env python3
"""
🔧 Enhanced Terminal Process Manager with Anti-Stuck Protection
Comprehensive solution to handle all terminal stuck scenarios and prevent shell freezing
"""

import os
import sys
import signal
import subprocess
import threading
import time
import psutil
import termios
import tty
import fcntl
import struct
import select
import queue
import logging
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

class ProcessState(Enum):
    """Process states for monitoring"""
    RUNNING = "running"
    SUSPENDED = "suspended"
    BACKGROUND = "background"
    ZOMBIE = "zombie"
    HUNG = "hung"
    TERMINATED = "terminated"
    ERROR = "error"

@dataclass
class ProcessInfo:
    """Process information structure"""
    pid: int
    command: str
    state: ProcessState
    start_time: float
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    is_foreground: bool = True
    is_blocking: bool = False
    tty_attached: bool = True
    last_activity: float = 0.0
    timeout: float = 30.0
    auto_background: bool = True
    resource_limit: Dict[str, float] = None

class TerminalState(Enum):
    """Terminal state monitoring"""
    NORMAL = "normal"
    RAW_MODE = "raw_mode"
    CANONICAL = "canonical"
    SUSPENDED = "suspended"
    HUNG = "hung"

class EnhancedTerminalManager:
    """
    Enhanced terminal manager that prevents shell from getting stuck
    Handles all common terminal stuck scenarios automatically
    """
    
    def __init__(self):
        self.processes: Dict[int, ProcessInfo] = {}
        self.terminal_state = TerminalState.NORMAL
        self.original_terminal_settings = None
        self.process_monitor_thread = None
        self.terminal_monitor_thread = None
        self.auto_recovery_enabled = True
        self.max_processes = 50
        self.resource_thresholds = {
            'cpu_percent': 90.0,
            'memory_percent': 80.0,
            'io_wait': 50.0,
            'response_time': 5.0
        }
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Save original terminal settings
        self._save_terminal_settings()
        
        # Start monitoring threads
        self._start_monitoring()
        
        # Set up signal handlers
        self._setup_signal_handlers()
    
    def _save_terminal_settings(self):
        """Save original terminal settings for recovery"""
        try:
            if sys.stdin.isatty():
                self.original_terminal_settings = termios.tcgetattr(sys.stdin.fileno())
                self.logger.info("Terminal settings saved")
        except Exception as e:
            self.logger.warning(f"Could not save terminal settings: {e}")
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGTSTP, self._signal_handler)
        signal.signal(signal.SIGCONT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle system signals"""
        if signum == signal.SIGINT:
            self.logger.info("SIGINT received, cleaning up processes...")
            self.cleanup_all_processes()
        elif signum == signal.SIGTERM:
            self.logger.info("SIGTERM received, shutting down...")
            self.shutdown()
        elif signum == signal.SIGTSTP:
            self.logger.info("SIGTSTP received, suspending...")
            self.suspend_all_processes()
        elif signum == signal.SIGCONT:
            self.logger.info("SIGCONT received, resuming...")
            self.resume_all_processes()
    
    def _start_monitoring(self):
        """Start background monitoring threads"""
        # Process monitoring thread
        self.process_monitor_thread = threading.Thread(
            target=self._process_monitor_loop,
            daemon=True
        )
        self.process_monitor_thread.start()
        
        # Terminal monitoring thread
        self.terminal_monitor_thread = threading.Thread(
            target=self._terminal_monitor_loop,
            daemon=True
        )
        self.terminal_monitor_thread.start()
        
        self.logger.info("Monitoring threads started")
    
    def _process_monitor_loop(self):
        """Main process monitoring loop"""
        while True:
            try:
                self._check_process_health()
                self._manage_resources()
                time.sleep(1)  # Check every second
            except Exception as e:
                self.logger.error(f"Error in process monitor: {e}")
                time.sleep(5)
    
    def _terminal_monitor_loop(self):
        """Main terminal monitoring loop"""
        while True:
            try:
                self._check_terminal_state()
                self._detect_terminal_issues()
                time.sleep(0.5)  # Check every 500ms
            except Exception as e:
                self.logger.error(f"Error in terminal monitor: {e}")
                time.sleep(2)
    
    def _check_process_health(self):
        """Check health of all monitored processes"""
        current_time = time.time()
        
        for pid, process_info in list(self.processes.items()):
            try:
                # Check if process still exists
                if not psutil.pid_exists(pid):
                    process_info.state = ProcessState.TERMINATED
                    del self.processes[pid]
                    continue
                
                # Get current process info
                proc = psutil.Process(pid)
                process_info.cpu_percent = proc.cpu_percent()
                process_info.memory_percent = proc.memory_percent()
                process_info.last_activity = current_time
                
                # Check for resource abuse
                if self._is_process_abusing_resources(process_info):
                    self.logger.warning(f"Process {pid} is abusing resources, taking action...")
                    self._handle_resource_abuse(process_info)
                
                # Check for hanging processes
                if self._is_process_hanging(process_info):
                    process_info.state = ProcessState.HUNG
                    self.logger.warning(f"Process {pid} appears to be hanging")
                    self._handle_hung_process(process_info)
                
            except psutil.NoSuchProcess:
                process_info.state = ProcessState.TERMINATED
                del self.processes[pid]
            except Exception as e:
                self.logger.error(f"Error checking process {pid}: {e}")
    
    def _is_process_abusing_resources(self, process_info: ProcessInfo) -> bool:
        """Check if process is abusing system resources"""
        if not process_info.resource_limit:
            return False
        
        if process_info.cpu_percent > self.resource_thresholds['cpu_percent']:
            return True
        
        if process_info.memory_percent > self.resource_thresholds['memory_percent']:
            return True
        
        return False
    
    def _is_process_hanging(self, process_info: ProcessInfo) -> bool:
        """Check if process appears to be hanging"""
        current_time = time.time()
        
        # Check if process has been running too long without activity
        if current_time - process_info.last_activity > process_info.timeout:
            return True
        
        # Check if process is consuming resources but not responding
        if process_info.cpu_percent > 0 and process_info.is_blocking:
            return True
        
        return False
    
    def _handle_resource_abuse(self, process_info: ProcessInfo):
        """Handle processes that are abusing resources"""
        try:
            if process_info.auto_background:
                self.logger.info(f"Auto-backgrounding resource-abusing process {process_info.pid}")
                self.background_process(process_info.pid)
            else:
                self.logger.warning(f"Terminating resource-abusing process {process_info.pid}")
                self.terminate_process(process_info.pid)
        except Exception as e:
            self.logger.error(f"Error handling resource abuse for {process_info.pid}: {e}")
    
    def _handle_hung_process(self, process_info: ProcessInfo):
        """Handle hanging processes"""
        try:
            if process_info.auto_background:
                self.logger.info(f"Auto-backgrounding hung process {process_info.pid}")
                self.background_process(process_info.pid)
            else:
                self.logger.warning(f"Terminating hung process {process_info.pid}")
                self.terminate_process(process_info.pid)
        except Exception as e:
            self.logger.error(f"Error handling hung process {process_info.pid}: {e}")
    
    def _check_terminal_state(self):
        """Check current terminal state"""
        try:
            if not sys.stdin.isatty():
                return
            
            # Check terminal mode
            fd = sys.stdin.fileno()
            mode = termios.tcgetattr(fd)
            
            # Check if in raw mode
            if mode[3] & termios.ICANON == 0:
                self.terminal_state = TerminalState.RAW_MODE
            else:
                self.terminal_state = TerminalState.NORMAL
                
        except Exception as e:
            self.logger.debug(f"Error checking terminal state: {e}")
    
    def _detect_terminal_issues(self):
        """Detect and fix terminal issues"""
        try:
            # Check for stuck terminal
            if self._is_terminal_stuck():
                self.logger.warning("Terminal appears to be stuck, attempting recovery...")
                self._recover_terminal()
            
            # Check for raw mode issues
            if self.terminal_state == TerminalState.RAW_MODE:
                self.logger.info("Terminal in raw mode, monitoring for issues...")
                if self._is_raw_mode_stuck():
                    self.logger.warning("Raw mode appears stuck, attempting recovery...")
                    self._recover_raw_mode()
                    
        except Exception as e:
            self.logger.error(f"Error detecting terminal issues: {e}")
    
    def _is_terminal_stuck(self) -> bool:
        """Check if terminal appears to be stuck"""
        try:
            # Try to read from stdin with timeout
            if select.select([sys.stdin], [], [], 0.1)[0]:
                return False
            
            # Check if any foreground process is blocking
            for process_info in self.processes.values():
                if process_info.is_foreground and process_info.is_blocking:
                    return True
            
            return False
        except Exception:
            return False
    
    def _is_raw_mode_stuck(self) -> bool:
        """Check if raw mode terminal is stuck"""
        try:
            # Try to write to terminal
            sys.stdout.write('\r')
            sys.stdout.flush()
            return False
        except Exception:
            return True
    
    def _recover_terminal(self):
        """Recover stuck terminal"""
        try:
            # Reset terminal to normal mode
            if self.original_terminal_settings:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.original_terminal_settings)
            
            # Send reset command
            os.system('reset')
            
            # Clear any pending input
            while select.select([sys.stdin], [], [], 0)[0]:
                sys.stdin.read(1)
            
            self.terminal_state = TerminalState.NORMAL
            self.logger.info("Terminal recovered successfully")
            
        except Exception as e:
            self.logger.error(f"Error recovering terminal: {e}")
    
    def _recover_raw_mode(self):
        """Recover stuck raw mode terminal"""
        try:
            # Reset to canonical mode
            if self.original_terminal_settings:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.original_terminal_settings)
            
            # Send stty sane command
            os.system('stty sane')
            
            self.terminal_state = TerminalState.NORMAL
            self.logger.info("Raw mode terminal recovered successfully")
            
        except Exception as e:
            self.logger.error(f"Error recovering raw mode terminal: {e}")
    
    def _manage_resources(self):
        """Manage system resources and prevent starvation"""
        try:
            # Check system resource usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Check for resource starvation
            if cpu_percent > self.resource_thresholds['cpu_percent']:
                self.logger.warning(f"High CPU usage detected: {cpu_percent}%")
                self._handle_high_cpu_usage()
            
            if memory.percent > self.resource_thresholds['memory_percent']:
                self.logger.warning(f"High memory usage detected: {memory.percent}%")
                self._handle_high_memory_usage()
                
        except Exception as e:
            self.logger.error(f"Error managing resources: {e}")
    
    def _handle_high_cpu_usage(self):
        """Handle high CPU usage"""
        try:
            # Find processes consuming most CPU
            high_cpu_processes = []
            for process_info in self.processes.values():
                if process_info.cpu_percent > 50:
                    high_cpu_processes.append(process_info)
            
            # Sort by CPU usage
            high_cpu_processes.sort(key=lambda x: x.cpu_percent, reverse=True)
            
            # Background or terminate high CPU processes
            for process_info in high_cpu_processes[:3]:  # Top 3
                if process_info.auto_background:
                    self.background_process(process_info.pid)
                else:
                    self.terminate_process(process_info.pid)
                    
        except Exception as e:
            self.logger.error(f"Error handling high CPU usage: {e}")
    
    def _handle_high_memory_usage(self):
        """Handle high memory usage"""
        try:
            # Find processes consuming most memory
            high_memory_processes = []
            for process_info in self.processes.values():
                if process_info.memory_percent > 30:
                    high_memory_processes.append(process_info)
            
            # Sort by memory usage
            high_memory_processes.sort(key=lambda x: x.memory_percent, reverse=True)
            
            # Background or terminate high memory processes
            for process_info in high_memory_processes[:3]:  # Top 3
                if process_info.auto_background:
                    self.background_process(process_info.pid)
                else:
                    self.terminate_process(process_info.pid)
                    
        except Exception as e:
            self.logger.error(f"Error handling high memory usage: {e}")
    
    def execute_command_safe(self, command: str, timeout: float = 30.0, 
                           auto_background: bool = True, resource_limit: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Execute command with comprehensive anti-stuck protection
        """
        try:
            # Check if we're at process limit
            if len(self.processes) >= self.max_processes:
                self.logger.warning("Process limit reached, cleaning up old processes...")
                self._cleanup_old_processes()
            
            # Start process with timeout protection
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid,  # Create new process group
                bufsize=1,
                universal_newlines=True
            )
            
            # Create process info
            process_info = ProcessInfo(
                pid=process.pid,
                command=command,
                state=ProcessState.RUNNING,
                start_time=time.time(),
                timeout=timeout,
                auto_background=auto_background,
                resource_limit=resource_limit or {}
            )
            
            # Add to monitoring
            self.processes[process.pid] = process_info
            
            # Start monitoring thread for this process
            monitor_thread = threading.Thread(
                target=self._monitor_single_process,
                args=(process, process_info),
                daemon=True
            )
            monitor_thread.start()
            
            self.logger.info(f"Started process {process.pid}: {command}")
            
            return {
                'success': True,
                'pid': process.pid,
                'command': command,
                'message': 'Process started successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Error starting process: {e}")
            return {
                'success': False,
                'error': str(e),
                'command': command
            }
    
    def _monitor_single_process(self, process: subprocess.Popen, process_info: ProcessInfo):
        """Monitor a single process for completion or issues"""
        try:
            # Wait for process with timeout
            stdout, stderr = process.communicate(timeout=process_info.timeout)
            
            # Process completed normally
            process_info.state = ProcessState.TERMINATED
            self.logger.info(f"Process {process.pid} completed successfully")
            
        except subprocess.TimeoutExpired:
            # Process timed out
            self.logger.warning(f"Process {process.pid} timed out, taking action...")
            self._handle_timeout_process(process, process_info)
            
        except Exception as e:
            # Process error
            self.logger.error(f"Process {process.pid} error: {e}")
            process_info.state = ProcessState.ERROR
            
        finally:
            # Clean up
            if process.pid in self.processes:
                del self.processes[process.pid]
    
    def _handle_timeout_process(self, process: subprocess.Popen, process_info: ProcessInfo):
        """Handle timed out processes"""
        try:
            if process_info.auto_background:
                # Try to background the process
                self.logger.info(f"Attempting to background timed out process {process.pid}")
                self.background_process(process.pid)
            else:
                # Terminate the process
                self.logger.info(f"Terminating timed out process {process.pid}")
                self.terminate_process(process.pid)
                
        except Exception as e:
            self.logger.error(f"Error handling timeout process {process.pid}: {e}")
            # Force kill as last resort
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except Exception:
                pass
    
    def background_process(self, pid: int) -> bool:
        """Move process to background"""
        try:
            if pid not in self.processes:
                return False
            
            process_info = self.processes[pid]
            
            # Send SIGTSTP to suspend
            os.kill(pid, signal.SIGTSTP)
            
            # Update state
            process_info.state = ProcessState.BACKGROUND
            process_info.is_foreground = False
            
            self.logger.info(f"Process {pid} moved to background")
            return True
            
        except Exception as e:
            self.logger.error(f"Error backgrounding process {pid}: {e}")
            return False
    
    def foreground_process(self, pid: int) -> bool:
        """Bring process to foreground"""
        try:
            if pid not in self.processes:
                return False
            
            process_info = self.processes[pid]
            
            # Send SIGCONT to resume
            os.kill(pid, signal.SIGCONT)
            
            # Update state
            process_info.state = ProcessState.RUNNING
            process_info.is_foreground = True
            
            self.logger.info(f"Process {pid} brought to foreground")
            return True
            
        except Exception as e:
            self.logger.error(f"Error foregrounding process {pid}: {e}")
            return False
    
    def suspend_process(self, pid: int) -> bool:
        """Suspend a process"""
        try:
            if pid not in self.processes:
                return False
            
            # Send SIGTSTP
            os.kill(pid, signal.SIGTSTP)
            
            # Update state
            self.processes[pid].state = ProcessState.SUSPENDED
            self.processes[pid].is_foreground = False
            
            self.logger.info(f"Process {pid} suspended")
            return True
            
        except Exception as e:
            self.logger.error(f"Error suspending process {pid}: {e}")
            return False
    
    def resume_process(self, pid: int) -> bool:
        """Resume a suspended process"""
        try:
            if pid not in self.processes:
                return False
            
            # Send SIGCONT
            os.kill(pid, signal.SIGCONT)
            
            # Update state
            self.processes[pid].state = ProcessState.RUNNING
            self.processes[pid].is_foreground = True
            
            self.logger.info(f"Process {pid} resumed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resuming process {pid}: {e}")
            return False
    
    def terminate_process(self, pid: int) -> bool:
        """Terminate a process gracefully"""
        try:
            if pid not in self.processes:
                return False
            
            # Send SIGTERM first
            os.kill(pid, signal.SIGTERM)
            
            # Wait a bit for graceful shutdown
            time.sleep(2)
            
            # Check if still running
            if psutil.pid_exists(pid):
                # Force kill if still running
                os.kill(pid, signal.SIGKILL)
            
            # Update state
            self.processes[pid].state = ProcessState.TERMINATED
            
            self.logger.info(f"Process {pid} terminated")
            return True
            
        except Exception as e:
            self.logger.error(f"Error terminating process {pid}: {e}")
            return False
    
    def kill_process(self, pid: int) -> bool:
        """Force kill a process"""
        try:
            if pid not in self.processes:
                return False
            
            # Force kill
            os.kill(pid, signal.SIGKILL)
            
            # Update state
            self.processes[pid].state = ProcessState.TERMINATED
            
            self.logger.info(f"Process {pid} force killed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error killing process {pid}: {e}")
            return False
    
    def list_processes(self) -> List[Dict[str, Any]]:
        """List all monitored processes"""
        processes = []
        for pid, process_info in self.processes.items():
            processes.append({
                'pid': pid,
                'command': process_info.command,
                'state': process_info.state.value,
                'cpu_percent': process_info.cpu_percent,
                'memory_percent': process_info.memory_percent,
                'is_foreground': process_info.is_foreground,
                'start_time': process_info.start_time,
                'uptime': time.time() - process_info.start_time
            })
        return processes
    
    def get_process_info(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific process"""
        if pid not in self.processes:
            return None
        
        process_info = self.processes[pid]
        return {
            'pid': pid,
            'command': process_info.command,
            'state': process_info.state.value,
            'cpu_percent': process_info.cpu_percent,
            'memory_percent': process_info.memory_percent,
            'is_foreground': process_info.is_foreground,
            'start_time': process_info.start_time,
            'uptime': time.time() - process_info.start_time,
            'timeout': process_info.timeout,
            'auto_background': process_info.auto_background,
            'resource_limit': process_info.resource_limit
        }
    
    def _cleanup_old_processes(self):
        """Clean up old or terminated processes"""
        current_time = time.time()
        to_remove = []
        
        for pid, process_info in self.processes.items():
            # Remove terminated processes
            if process_info.state in [ProcessState.TERMINATED, ProcessState.ERROR]:
                to_remove.append(pid)
            
            # Remove very old processes
            elif current_time - process_info.start_time > 3600:  # 1 hour
                to_remove.append(pid)
        
        for pid in to_remove:
            del self.processes[pid]
        
        if to_remove:
            self.logger.info(f"Cleaned up {len(to_remove)} old processes")
    
    def cleanup_all_processes(self):
        """Clean up all monitored processes"""
        for pid in list(self.processes.keys()):
            try:
                self.terminate_process(pid)
            except Exception as e:
                self.logger.error(f"Error cleaning up process {pid}: {e}")
    
    def suspend_all_processes(self):
        """Suspend all running processes"""
        for pid in list(self.processes.keys()):
            try:
                if self.processes[pid].state == ProcessState.RUNNING:
                    self.suspend_process(pid)
            except Exception as e:
                self.logger.error(f"Error suspending process {pid}: {e}")
    
    def resume_all_processes(self):
        """Resume all suspended processes"""
        for pid in list(self.processes.keys()):
            try:
                if self.processes[pid].state == ProcessState.SUSPENDED:
                    self.resume_process(pid)
            except Exception as e:
                self.logger.error(f"Error resuming process {pid}: {e}")
    
    def shutdown(self):
        """Shutdown the terminal manager"""
        self.logger.info("Shutting down terminal manager...")
        
        # Stop monitoring threads
        self.process_monitor_thread = None
        self.terminal_monitor_thread = None
        
        # Clean up all processes
        self.cleanup_all_processes()
        
        # Restore terminal settings
        if self.original_terminal_settings:
            try:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.original_terminal_settings)
            except Exception:
                pass
        
        self.logger.info("Terminal manager shutdown complete")

# Global instance
terminal_manager = EnhancedTerminalManager()

def get_terminal_manager():
    """Get the global terminal manager instance"""
    return terminal_manager

# Convenience functions
def execute_safe(command: str, timeout: float = 30.0, auto_background: bool = True) -> Dict[str, Any]:
    """Execute command safely with anti-stuck protection"""
    return terminal_manager.execute_command_safe(command, timeout, auto_background)

def background_process(pid: int) -> bool:
    """Move process to background"""
    return terminal_manager.background_process(pid)

def foreground_process(pid: int) -> bool:
    """Bring process to foreground"""
    return terminal_manager.foreground_process(pid)

def suspend_process(pid: int) -> bool:
    """Suspend a process"""
    return terminal_manager.suspend_process(pid)

def resume_process(pid: int) -> bool:
    """Resume a suspended process"""
    return terminal_manager.resume_process(pid)

def terminate_process(pid: int) -> bool:
    """Terminate a process gracefully"""
    return terminal_manager.terminate_process(pid)

def kill_process(pid: int) -> bool:
    """Force kill a process"""
    return terminal_manager.kill_process(pid)

def list_processes() -> List[Dict[str, Any]]:
    """List all monitored processes"""
    return terminal_manager.list_processes()

def get_process_info(pid: int) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific process"""
    return terminal_manager.get_process_info(pid)

def cleanup_all_processes():
    """Clean up all monitored processes"""
    terminal_manager.cleanup_all_processes()

def shutdown_terminal_manager():
    """Shutdown the terminal manager"""
    terminal_manager.shutdown()