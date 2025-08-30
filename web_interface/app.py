#!/usr/bin/env python3
"""
🚀 Unified AI Shell Web Interface
A powerful web-based control center for your AI terminal with voice control
"""

import os
import json
import asyncio
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import speech_recognition as sr
from pydub import AudioSegment
import numpy as np
import cv2
import psutil
import GPUtil

# Import our AI Shell components
import sys
sys.path.append('/workspace')
from config.config_manager import ConfigManager
from core.ai_manager import AIManager
from core.system_controller import SystemController
from core.shell import AIShell

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-super-secret-key-change-this-in-production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize AI Shell components
config_manager = ConfigManager()
ai_manager = AIManager(config_manager)
system_controller = SystemController()
ai_shell = AIShell(config_manager)

# Global variables for terminal state
terminal_output = []
terminal_history = []
active_processes = {}
voice_recognizer = sr.Recognizer()
system_monitoring = True

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# Simple user management (in production, use a proper database)
users = {
    'admin': User('admin', 'admin', generate_password_hash('admin123'))
}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

@app.route('/')
@login_required
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = users.get(username)
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        
        return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/system/status')
@login_required
def system_status():
    """Get real-time system status"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get GPU info if available
        gpu_info = []
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                gpu_info.append({
                    'name': gpu.name,
                    'load': gpu.load * 100,
                    'memory_used': gpu.memoryUsed,
                    'memory_total': gpu.memoryTotal,
                    'temperature': gpu.temperature
                })
        except:
            pass
        
        return jsonify({
            'cpu': {
                'percent': cpu_percent,
                'count': psutil.cpu_count(),
                'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {}
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': (disk.used / disk.total) * 100
            },
            'gpu': gpu_info,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/terminal/execute', methods=['POST'])
@login_required
def execute_terminal_command():
    """Execute terminal command and return output"""
    try:
        data = request.get_json()
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({'error': 'No command provided'}), 400
        
        # Check for dangerous commands
        dangerous_commands = ['rm -rf /', 'dd if=/dev/zero', 'mkfs', 'fdisk']
        if any(dangerous in command.lower() for dangerous in dangerous_commands):
            return jsonify({'error': 'Dangerous command blocked'}), 403
        
        # Execute command
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd='/workspace'
        )
        
        stdout, stderr = process.communicate()
        
        # Add to terminal history
        terminal_history.append({
            'command': command,
            'output': stdout,
            'error': stderr,
            'timestamp': datetime.now().isoformat(),
            'exit_code': process.returncode
        })
        
        # Keep only last 100 commands
        if len(terminal_history) > 100:
            terminal_history.pop(0)
        
        # Emit to WebSocket for real-time updates
        socketio.emit('terminal_output', {
            'command': command,
            'output': stdout,
            'error': stderr,
            'timestamp': datetime.now().isoformat(),
            'exit_code': process.returncode
        })
        
        return jsonify({
            'success': True,
            'output': stdout,
            'error': stderr,
            'exit_code': process.returncode
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/terminal/history')
@login_required
def get_terminal_history():
    """Get terminal command history"""
    return jsonify(terminal_history)

@app.route('/api/ai/chat', methods=['POST'])
@login_required
def ai_chat():
    """Send message to AI and get response"""
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
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/transcribe', methods=['POST'])
@login_required
def transcribe_audio():
    """Transcribe uploaded audio file"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        # Save temporary audio file
        temp_path = f'/tmp/voice_{int(time.time())}.wav'
        audio_file.save(temp_path)
        
        # Transcribe using speech recognition
        with sr.AudioFile(temp_path) as source:
            audio = voice_recognizer.record(source)
        
        # Try multiple recognition engines
        text = None
        try:
            text = voice_recognizer.recognize_google(audio)
        except:
            try:
                text = voice_recognizer.recognize_sphinx(audio)
            except:
                pass
        
        # Clean up
        os.remove(temp_path)
        
        if text:
            return jsonify({
                'success': True,
                'transcription': text,
                'confidence': 0.9
            })
        else:
            return jsonify({'error': 'Could not transcribe audio'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/list')
@login_required
def list_files():
    """List files in current directory"""
    try:
        path = request.args.get('path', '/workspace')
        files = []
        
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            stat = os.stat(item_path)
            
            files.append({
                'name': item,
                'path': item_path,
                'is_dir': os.path.isdir(item_path),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'permissions': oct(stat.st_mode)[-3:]
            })
        
        return jsonify(files)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/read')
@login_required
def read_file():
    """Read file contents"""
    try:
        file_path = request.args.get('path', '')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'content': content,
            'path': file_path
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/write', methods=['POST'])
@login_required
def write_file():
    """Write content to file"""
    try:
        data = request.get_json()
        file_path = data.get('path', '')
        content = data.get('content', '')
        
        if not file_path:
            return jsonify({'error': 'No file path provided'}), 400
        
        # Ensure we're writing to workspace or safe directories
        safe_dirs = ['/workspace', '/tmp', '/home']
        if not any(file_path.startswith(safe_dir) for safe_dir in safe_dirs):
            return jsonify({'error': 'Access denied to this directory'}), 403
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')
    emit('status', {'message': 'Connected to AI Shell Web Interface'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')

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
    """Handle voice command from client"""
    try:
        command = data.get('command', '')
        if command:
            # Execute the voice command
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            # Emit result back to client
            emit('voice_command_result', {
                'command': command,
                'output': stdout,
                'error': stderr,
                'exit_code': process.returncode
            })
            
    except Exception as e:
        emit('voice_command_error', {'error': str(e)})

def start_system_monitoring():
    """Background thread for system monitoring"""
    while system_monitoring:
        try:
            # Get system status
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Emit to all connected clients
            socketio.emit('system_update', {
                'cpu': cpu_percent,
                'memory': memory.percent,
                'timestamp': datetime.now().isoformat()
            })
            
            time.sleep(5)  # Update every 5 seconds
            
        except Exception as e:
            print(f'System monitoring error: {e}')
            time.sleep(10)

if __name__ == '__main__':
    # Start system monitoring in background
    monitoring_thread = threading.Thread(target=start_system_monitoring, daemon=True)
    monitoring_thread.start()
    
    print("🚀 Starting Unified AI Shell Web Interface...")
    print("📱 Access at: http://localhost:5000")
    print("🔐 Default login: admin / admin123")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)