#!/usr/bin/env python3
"""
🚀 Enhanced Unified AI Shell Web Interface
A production-ready web-based control center with robust error handling,
advanced PC control capabilities, and comprehensive security features
"""

import os
import json
import asyncio
import subprocess
import threading
import time
import logging
import traceback
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from functools import wraps
import signal
import sys

# Flask and extensions
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, abort, g
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException

# System and monitoring
import psutil
import GPUtil
import platform
import socket as socket_lib
import requests
from requests.exceptions import RequestException

# Voice and audio processing
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    print("Warning: Speech recognition not available")

try:
    from pydub import AudioSegment
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("Warning: Audio processing not available")

# Import our AI Shell components
import sys
sys.path.append('/workspace')
try:
    from config.config_manager import ConfigManager
    from core.ai_manager import AIManager
    from core.system_controller import SystemController
    from core.shell import AIShell
    AI_SHELL_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI Shell components not available: {e}")
    AI_SHELL_AVAILABLE = False

# Enhanced configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB max file size
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Security settings
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_TIMEOUT_MINUTES = 15
    RATE_LIMIT_REQUESTS = 100  # requests per minute
    RATE_LIMIT_WINDOW = 60  # seconds
    
    # System control settings
    ALLOWED_COMMANDS = [
        'ls', 'pwd', 'whoami', 'date', 'uptime', 'ps', 'top', 'htop',
        'df', 'du', 'free', 'cat', 'head', 'tail', 'grep', 'find',
        'mkdir', 'rmdir', 'touch', 'cp', 'mv', 'rm', 'chmod', 'chown',
        'tar', 'zip', 'unzip', 'wget', 'curl', 'git', 'docker', 'kubectl'
    ]
    
    BLOCKED_COMMANDS = [
        'rm -rf /', 'dd if=/dev/zero', 'mkfs', 'fdisk', 'format',
        'shutdown', 'reboot', 'halt', 'poweroff', 'init 0', 'init 6',
        'sudo rm -rf', 'sudo dd', 'sudo mkfs', 'sudo fdisk'
    ]
    
    SAFE_DIRECTORIES = ['/workspace', '/tmp', '/home', '/var/log', '/opt']

# Initialize Flask app with enhanced configuration
app = Flask(__name__)
app.config.from_object(Config)

# Enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/web_interface.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize extensions
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Enhanced user management
class User(UserMixin):
    def __init__(self, id, username, password_hash, role='user', permissions=None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.permissions = permissions or []
        self.login_attempts = 0
        self.locked_until = None
        self.last_activity = datetime.now()

# Enhanced users with roles and permissions
users = {
    'admin': User('admin', 'admin', generate_password_hash('admin123'), 'admin', ['all']),
    'user': User('user', 'user', generate_password_hash('user123'), 'user', ['read', 'execute']),
    'developer': User('developer', 'developer', generate_password_hash('dev123'), 'developer', ['read', 'write', 'execute'])
}

# Rate limiting and security
class RateLimiter:
    def __init__(self):
        self.requests = {}
        self.lock = threading.Lock()
    
    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        with self.lock:
            if ip not in self.requests:
                self.requests[ip] = []
            
            # Remove old requests
            self.requests[ip] = [req_time for req_time in self.requests[ip] 
                               if now - req_time < Config.RATE_LIMIT_WINDOW]
            
            # Check if limit exceeded
            if len(self.requests[ip]) >= Config.RATE_LIMIT_REQUESTS:
                return False
            
            # Add current request
            self.requests[ip].append(now)
            return True

rate_limiter = RateLimiter()

# Enhanced error handling decorator
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
    return decorated_function

# Enhanced security decorator
def require_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            if 'all' in current_user.permissions or permission in current_user.permissions:
                return f(*args, **kwargs)
            else:
                abort(403)
        return decorated_function
    return decorator

# Enhanced rate limiting decorator
def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        if not rate_limiter.is_allowed(ip):
            return jsonify({'error': 'Rate limit exceeded'}), 429
        return f(*args, **kwargs)
    return decorated_function

# Enhanced command validation
class CommandValidator:
    @staticmethod
    def is_safe_command(command: str) -> Tuple[bool, str]:
        """Validate if a command is safe to execute"""
        command_lower = command.lower().strip()
        
        # Check for blocked commands
        for blocked in Config.BLOCKED_COMMANDS:
            if blocked in command_lower:
                return False, f"Command blocked for security: {blocked}"
        
        # Check if command starts with allowed commands
        for allowed in Config.ALLOWED_COMMANDS:
            if command_lower.startswith(allowed):
                return True, "Command allowed"
        
        # Check for sudo usage
        if command_lower.startswith('sudo '):
            return False, "Sudo commands are not allowed for security"
        
        # Check for shell injection attempts
        dangerous_chars = [';', '&&', '||', '|', '>', '<', '`', '$(']
        for char in dangerous_chars:
            if char in command:
                return False, f"Dangerous character detected: {char}"
        
        return False, "Command not in allowed list"

# Enhanced system controller
class EnhancedSystemController:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            info = {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'architecture': platform.architecture(),
                'processor': platform.processor(),
                'hostname': platform.node(),
                'python_version': platform.python_version(),
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                'users': [user.name for user in psutil.users()],
                'cpu_count': psutil.cpu_count(),
                'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
                'memory': psutil.virtual_memory()._asdict(),
                'swap': psutil.swap_memory()._asdict(),
                'disk_partitions': [part._asdict() for part in psutil.disk_partitions()],
                'network_interfaces': self._get_network_info(),
                'environment_variables': dict(os.environ),
                'timestamp': datetime.now().isoformat()
            }
            
            # Add GPU info if available
            try:
                gpus = GPUtil.getGPUs()
                info['gpus'] = [gpu.__dict__ for gpu in gpus]
            except:
                info['gpus'] = []
            
            return info
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return {'error': str(e)}
    
    def _get_network_info(self) -> Dict[str, Any]:
        """Get detailed network information"""
        try:
            info = {}
            for interface, addresses in psutil.net_if_addrs().items():
                info[interface] = {
                    'addresses': [addr._asdict() for addr in addresses],
                    'stats': psutil.net_if_stats()[interface]._asdict() if interface in psutil.net_if_stats() else {}
                }
            
            # Get network connections
            connections = psutil.net_connections()
            info['connections'] = [conn._asdict() for conn in connections]
            
            return info
        except Exception as e:
            self.logger.error(f"Error getting network info: {e}")
            return {'error': str(e)}
    
    def execute_command_safe(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute command with enhanced safety and monitoring"""
        try:
            # Validate command
            is_safe, message = CommandValidator.is_safe_command(command)
            if not is_safe:
                return {'success': False, 'error': message, 'command': command}
            
            # Execute with timeout and resource limits
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd='/workspace',
                preexec_fn=os.setsid  # Create new process group
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                # Kill process group if timeout
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                
                return {
                    'success': False,
                    'error': f'Command timed out after {timeout} seconds',
                    'command': command,
                    'exit_code': -1
                }
            
            return {
                'success': True,
                'command': command,
                'output': stdout,
                'error': stderr,
                'exit_code': exit_code,
                'execution_time': time.time(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error executing command '{command}': {e}")
            return {
                'success': False,
                'error': str(e),
                'command': command,
                'exit_code': -1
            }
    
    def get_process_info(self) -> List[Dict[str, Any]]:
        """Get detailed process information"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    proc_info = proc.info
                    proc_info['create_time'] = datetime.fromtimestamp(proc.create_time()).isoformat()
                    proc_info['memory_info'] = proc.memory_info()._asdict()
                    proc_info['cpu_times'] = proc.cpu_times()._asdict()
                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)
        except Exception as e:
            self.logger.error(f"Error getting process info: {e}")
            return []
    
    def kill_process(self, pid: int) -> Dict[str, Any]:
        """Safely kill a process"""
        try:
            if not isinstance(pid, int) or pid <= 0:
                return {'success': False, 'error': 'Invalid PID'}
            
            proc = psutil.Process(pid)
            proc.terminate()
            
            try:
                proc.wait(timeout=5)
                return {'success': True, 'message': f'Process {pid} terminated'}
            except psutil.TimeoutExpired:
                proc.kill()
                return {'success': True, 'message': f'Process {pid} killed'}
                
        except psutil.NoSuchProcess:
            return {'success': False, 'error': f'Process {pid} not found'}
        except psutil.AccessDenied:
            return {'success': False, 'error': f'Access denied to process {pid}'}
        except Exception as e:
            self.logger.error(f"Error killing process {pid}: {e}")
            return {'success': False, 'error': str(e)}

# Initialize enhanced components
enhanced_system_controller = EnhancedSystemController()

# Initialize AI Shell components if available
if AI_SHELL_AVAILABLE:
    try:
        config_manager = ConfigManager()
        ai_manager = AIManager(config_manager)
        system_controller = SystemController()
        ai_shell = AIShell(config_manager)
    except Exception as e:
        logger.error(f"Failed to initialize AI Shell components: {e}")
        AI_SHELL_AVAILABLE = False

# Global variables
terminal_output = []
terminal_history = []
active_processes = {}
system_monitoring = True
voice_recognizer = None

if SPEECH_AVAILABLE:
    try:
        voice_recognizer = sr.Recognizer()
    except Exception as e:
        logger.error(f"Failed to initialize voice recognition: {e}")

# Enhanced user loader
@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

# Enhanced login with rate limiting and security
@app.route('/login', methods=['GET', 'POST'])
@rate_limit
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            return render_template('login.html', error='Username and password required')
        
        user = users.get(username)
        if not user:
            return render_template('login.html', error='Invalid credentials')
        
        # Check if account is locked
        if user.locked_until and datetime.now() < user.locked_until:
            remaining = user.locked_until - datetime.now()
            return render_template('login.html', 
                                error=f'Account locked. Try again in {remaining.seconds//60} minutes')
        
        # Check password
        if not check_password_hash(user.password_hash, password):
            user.login_attempts += 1
            
            # Lock account if too many failed attempts
            if user.login_attempts >= Config.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.now() + timedelta(minutes=Config.LOGIN_TIMEOUT_MINUTES)
                logger.warning(f"Account {username} locked due to too many failed attempts")
                return render_template('login.html', 
                                    error=f'Account locked for {Config.LOGIN_TIMEOUT_MINUTES} minutes')
            
            return render_template('login.html', 
                                error=f'Invalid credentials. {Config.MAX_LOGIN_ATTEMPTS - user.login_attempts} attempts remaining')
        
        # Reset login attempts on successful login
        user.login_attempts = 0
        user.last_activity = datetime.now()
        
        login_user(user)
        logger.info(f"User {username} logged in successfully")
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logger.info(f"User {current_user.username} logged out")
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
@rate_limit
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

# Enhanced API endpoints with error handling and security
@app.route('/api/system/status')
@login_required
@rate_limit
@handle_errors
def system_status():
    """Get real-time system status with enhanced monitoring"""
    try:
        # Get basic system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get detailed system info
        system_info = enhanced_system_controller.get_system_info()
        
        # Get process count
        process_count = len(psutil.pids())
        
        # Get network stats
        network_stats = psutil.net_io_counters()
        
        return jsonify({
            'cpu': {
                'percent': cpu_percent,
                'count': psutil.cpu_count(),
                'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
                'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else []
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used,
                'free': memory.free,
                'cached': getattr(memory, 'cached', 0),
                'buffers': getattr(memory, 'buffers', 0)
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': (disk.used / disk.total) * 100
            },
            'system': system_info,
            'processes': {
                'count': process_count,
                'running': len([p for p in psutil.process_iter() if p.status() == 'running'])
            },
            'network': {
                'bytes_sent': network_stats.bytes_sent,
                'bytes_recv': network_stats.bytes_recv,
                'packets_sent': network_stats.packets_sent,
                'packets_recv': network_stats.packets_recv
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/terminal/execute', methods=['POST'])
@login_required
@rate_limit
@require_permission('execute')
@handle_errors
def execute_terminal_command():
    """Execute terminal command with enhanced safety and monitoring"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        command = data.get('command', '').strip()
        if not command:
            return jsonify({'error': 'No command provided'}), 400
        
        # Log command execution
        logger.info(f"User {current_user.username} executing command: {command}")
        
        # Execute command safely
        result = enhanced_system_controller.execute_command_safe(command)
        
        if result['success']:
            # Add to terminal history
            terminal_history.append({
                'command': command,
                'output': result['output'],
                'error': result['error'],
                'timestamp': result['timestamp'],
                'exit_code': result['exit_code'],
                'user': current_user.username,
                'execution_time': result['execution_time']
            })
            
            # Keep only last 1000 commands
            if len(terminal_history) > 1000:
                terminal_history.pop(0)
            
            # Emit to WebSocket for real-time updates
            socketio.emit('terminal_output', {
                'command': command,
                'output': result['output'],
                'error': result['error'],
                'timestamp': result['timestamp'],
                'exit_code': result['exit_code'],
                'user': current_user.username
            })
            
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/terminal/history')
@login_required
@rate_limit
@handle_errors
def get_terminal_history():
    """Get terminal command history with pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        history_page = terminal_history[start_idx:end_idx]
        total_pages = (len(terminal_history) + per_page - 1) // per_page
        
        return jsonify({
            'history': history_page,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': len(terminal_history),
                'total_pages': total_pages
            }
        })
    except Exception as e:
        logger.error(f"Error getting terminal history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/chat', methods=['POST'])
@login_required
@rate_limit
@handle_errors
def ai_chat():
    """Send message to AI with enhanced error handling"""
    if not AI_SHELL_AVAILABLE:
        return jsonify({'error': 'AI Shell not available'}), 503
    
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get AI response
        response, model = ai_manager.get_ai_response(message)
        
        return jsonify({
            'success': True,
            'response': response,
            'model': model,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/transcribe', methods=['POST'])
@login_required
@rate_limit
@handle_errors
def transcribe_audio():
    """Transcribe uploaded audio file with enhanced error handling"""
    if not SPEECH_AVAILABLE or not voice_recognizer:
        return jsonify({'error': 'Voice recognition not available'}), 503
    
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        # Validate file type
        if not audio_file.filename.lower().endswith(('.wav', '.mp3', '.ogg', '.flac')):
            return jsonify({'error': 'Unsupported audio format'}), 400
        
        # Save temporary audio file
        temp_path = f'/tmp/voice_{int(time.time())}_{secrets.token_hex(8)}.wav'
        audio_file.save(temp_path)
        
        try:
            # Transcribe using speech recognition
            with sr.AudioFile(temp_path) as source:
                audio = voice_recognizer.record(source)
            
            # Try multiple recognition engines
            text = None
            engine_used = None
            
            try:
                text = voice_recognizer.recognize_google(audio)
                engine_used = 'Google'
            except sr.UnknownValueError:
                try:
                    text = voice_recognizer.recognize_sphinx(audio)
                    engine_used = 'Sphinx'
                except:
                    pass
            
            if text:
                return jsonify({
                    'success': True,
                    'transcription': text,
                    'engine': engine_used,
                    'confidence': 0.9,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({'error': 'Could not transcribe audio'}), 400
                
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/processes')
@login_required
@rate_limit
@handle_errors
def get_processes():
    """Get detailed process information"""
    try:
        processes = enhanced_system_controller.get_process_info()
        return jsonify({
            'processes': processes,
            'count': len(processes),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting processes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/processes/<int:pid>/kill', methods=['POST'])
@login_required
@rate_limit
@require_permission('execute')
@handle_errors
def kill_process(pid):
    """Kill a specific process"""
    try:
        result = enhanced_system_controller.kill_process(pid)
        if result['success']:
            logger.info(f"User {current_user.username} killed process {pid}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error killing process {pid}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/list')
@login_required
@rate_limit
@handle_errors
def list_files():
    """List files in current directory with enhanced security"""
    try:
        path = request.args.get('path', '/workspace')
        
        # Security check - ensure path is within safe directories
        safe_path = False
        for safe_dir in Config.SAFE_DIRECTORIES:
            if path.startswith(safe_dir):
                safe_path = True
                break
        
        if not safe_path:
            return jsonify({'error': 'Access denied to this directory'}), 403
        
        if not os.path.exists(path):
            return jsonify({'error': 'Directory not found'}), 404
        
        files = []
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                try:
                    stat = os.stat(item_path)
                    files.append({
                        'name': item,
                        'path': item_path,
                        'is_dir': os.path.isdir(item_path),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'permissions': oct(stat.st_mode)[-3:],
                        'owner': stat.st_uid,
                        'group': stat.st_gid
                    })
                except OSError:
                    # Skip files we can't access
                    continue
            
            return jsonify(files)
        except PermissionError:
            return jsonify({'error': 'Permission denied'}), 403
            
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/read')
@login_required
@rate_limit
@handle_errors
def read_file():
    """Read file contents with enhanced security"""
    try:
        file_path = request.args.get('path', '')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Security check
        safe_path = False
        for safe_dir in Config.SAFE_DIRECTORIES:
            if file_path.startswith(safe_dir):
                safe_path = True
                break
        
        if not safe_path:
            return jsonify({'error': 'Access denied to this file'}), 403
        
        # Check file size (limit to 10MB for reading)
        file_size = os.path.getsize(file_path)
        if file_size > 10 * 1024 * 1024:
            return jsonify({'error': 'File too large to read'}), 413
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return jsonify({
                'success': True,
                'content': content,
                'path': file_path,
                'size': file_size,
                'timestamp': datetime.now().isoformat()
            })
        except UnicodeDecodeError:
            return jsonify({'error': 'File contains binary data or unsupported encoding'}), 400
        except PermissionError:
            return jsonify({'error': 'Permission denied'}), 403
            
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/write', methods=['POST'])
@login_required
@rate_limit
@require_permission('write')
@handle_errors
def write_file():
    """Write content to file with enhanced security"""
    try:
        data = request.get_json()
        file_path = data.get('path', '')
        content = data.get('content', '')
        
        if not file_path:
            return jsonify({'error': 'No file path provided'}), 400
        
        # Security check
        safe_path = False
        for safe_dir in Config.SAFE_DIRECTORIES:
            if file_path.startswith(safe_dir):
                safe_path = True
                break
        
        if not safe_path:
            return jsonify({'error': 'Access denied to this directory'}), 403
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"User {current_user.username} wrote to file: {file_path}")
            return jsonify({'success': True, 'message': 'File written successfully'})
        except PermissionError:
            return jsonify({'error': 'Permission denied'}), 403
            
    except Exception as e:
        logger.error(f"Error writing file: {e}")
        return jsonify({'error': str(e)}), 500

# Enhanced WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection with enhanced logging"""
    client_ip = request.remote_addr
    logger.info(f'Client connected: {request.sid} from {client_ip}')
    emit('status', {'message': 'Connected to Enhanced AI Shell Web Interface'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f'Client disconnected: {request.sid}')
    # Clean up any user-specific data

@socketio.on('join_terminal')
def handle_join_terminal():
    """Join terminal room for real-time updates"""
    join_room('terminal')
    emit('terminal_status', {'message': 'Joined terminal room'})

@socketio.on('leave_terminal')
def handle_leave_terminal():
    """Leave terminal room"""
    leave_room('terminal')

@socketio.on('voice_command')
def handle_voice_command(data):
    """Handle voice command from client with enhanced validation"""
    try:
        command = data.get('command', '').strip()
        if not command:
            emit('voice_command_error', {'error': 'No command provided'})
            return
        
        # Validate command
        is_safe, message = CommandValidator.is_safe_command(command)
        if not is_safe:
            emit('voice_command_error', {'error': message})
            return
        
        # Execute command safely
        result = enhanced_system_controller.execute_command_safe(command)
        
        # Emit result back to client
        emit('voice_command_result', result)
        
        # Log voice command
        logger.info(f"Voice command executed: {command} by {request.sid}")
        
    except Exception as e:
        logger.error(f"Error handling voice command: {e}")
        emit('voice_command_error', {'error': str(e)})

# Enhanced system monitoring
def start_system_monitoring():
    """Background thread for enhanced system monitoring"""
    while system_monitoring:
        try:
            # Get system status
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Get additional metrics
            disk_usage = psutil.disk_usage('/')
            network_io = psutil.net_io_counters()
            
            # Emit to all connected clients
            socketio.emit('system_update', {
                'cpu': cpu_percent,
                'memory': memory.percent,
                'disk': (disk_usage.used / disk_usage.total) * 100,
                'network': {
                    'bytes_sent': network_io.bytes_sent,
                    'bytes_recv': network_io.bytes_recv
                },
                'timestamp': datetime.now().isoformat()
            })
            
            time.sleep(5)  # Update every 5 seconds
            
        except Exception as e:
            logger.error(f'System monitoring error: {e}')
            time.sleep(10)

# Enhanced error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}")
    return jsonify({'error': 'An unexpected error occurred'}), 500

# Graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Shutdown signal received, cleaning up...")
    global system_monitoring
    system_monitoring = False
    
    # Clean up resources
    if 'socketio' in globals():
        socketio.stop()
    
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('temp', exist_ok=True)
    
    # Start system monitoring in background
    monitoring_thread = threading.Thread(target=start_system_monitoring, daemon=True)
    monitoring_thread.start()
    
    logger.info("🚀 Starting Enhanced Unified AI Shell Web Interface...")
    logger.info("📱 Access at: http://localhost:5000")
    logger.info("🔐 Default login: admin / admin123")
    logger.info("🛡️ Enhanced security and error handling enabled")
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Failed to start web interface: {e}")
        sys.exit(1)