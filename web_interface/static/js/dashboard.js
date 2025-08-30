/**
 * 🚀 Unified AI Shell Web Interface - Dashboard JavaScript
 * Handles all interactive functionality including WebSocket communication,
 * voice recognition, terminal control, and system monitoring
 */

// Global variables
let socket;
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let isListening = false;
let terminalHistory = [];
let currentPath = '/workspace';

// Initialize the dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    initializeWebSocket();
    loadInitialData();
    startSystemMonitoring();
});

/**
 * Initialize dashboard components and event listeners
 */
function initializeDashboard() {
    console.log('🚀 Initializing Unified AI Shell Dashboard...');
    
    // Add event listeners
    document.getElementById('commandInput').addEventListener('keypress', handleCommandEnter);
    document.getElementById('filePath').addEventListener('keypress', handlePathEnter);
    document.getElementById('aiMessage').addEventListener('keypress', handleAIEnter);
    
    // Initialize tooltips
    initializeTooltips();
    
    // Load saved settings
    loadSettings();
    
    console.log('✅ Dashboard initialized successfully');
}

/**
 * Initialize WebSocket connection for real-time updates
 */
function initializeWebSocket() {
    try {
        socket = io();
        
        socket.on('connect', function() {
            console.log('🔌 WebSocket connected');
            showNotification('Connected to AI Shell', 'success');
            joinTerminalRoom();
        });
        
        socket.on('disconnect', function() {
            console.log('❌ WebSocket disconnected');
            showNotification('Disconnected from AI Shell', 'warning');
        });
        
        socket.on('terminal_output', function(data) {
            displayTerminalOutput(data);
        });
        
        socket.on('system_update', function(data) {
            updateSystemStatus(data);
        });
        
        socket.on('voice_command_result', function(data) {
            handleVoiceCommandResult(data);
        });
        
        socket.on('voice_command_error', function(data) {
            showNotification('Voice command error: ' + data.error, 'danger');
        });
        
        socket.on('status', function(data) {
            console.log('Status:', data.message);
        });
        
        socket.on('terminal_status', function(data) {
            console.log('Terminal status:', data.message);
        });
        
    } catch (error) {
        console.error('❌ WebSocket initialization failed:', error);
        showNotification('WebSocket connection failed', 'danger');
    }
}

/**
 * Join terminal room for real-time updates
 */
function joinTerminalRoom() {
    if (socket) {
        socket.emit('join_terminal');
    }
}

/**
 * Load initial data for the dashboard
 */
function loadInitialData() {
    // Load file list
    listFiles();
    
    // Load terminal history
    loadTerminalHistory();
    
    // Get system status
    updateSystemStatusFromAPI();
    
    // Get network information
    getNetworkInfo();
}

/**
 * Start system monitoring loop
 */
function startSystemMonitoring() {
    setInterval(() => {
        updateSystemStatusFromAPI();
    }, 5000); // Update every 5 seconds
}

/**
 * Handle command input enter key press
 */
function handleCommandEnter(event) {
    if (event.key === 'Enter') {
        executeCommandFromInput();
    }
}

/**
 * Handle file path enter key press
 */
function handlePathEnter(event) {
    if (event.key === 'Enter') {
        listFiles();
    }
}

/**
 * Handle AI message enter key press
 */
function handleAIEnter(event) {
    if (event.key === 'Enter') {
        sendAIMessage();
    }
}

/**
 * Execute command from input field
 */
function executeCommandFromInput() {
    const commandInput = document.getElementById('commandInput');
    const command = commandInput.value.trim();
    
    if (command) {
        executeCommand(command);
        commandInput.value = '';
    }
}

/**
 * Execute a terminal command
 */
function executeCommand(command) {
    if (!command.trim()) return;
    
    // Add command to terminal display
    addTerminalLine('🚀 AI Shell>', command, 'command');
    
    // Show loading state
    showTerminalLoading();
    
    // Send command to server
    fetch('/api/terminal/execute', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command: command })
    })
    .then(response => response.json())
    .then(data => {
        hideTerminalLoading();
        
        if (data.success) {
            // Display output
            if (data.output) {
                addTerminalLine('📤 Output:', data.output, 'output');
            }
            if (data.error) {
                addTerminalLine('❌ Error:', data.error, 'error');
            }
            
            // Update file list if command affects files
            if (command.includes('ls') || command.includes('cd') || command.includes('mkdir') || command.includes('rm')) {
                setTimeout(listFiles, 1000);
            }
        } else {
            addTerminalLine('❌ Error:', data.error, 'error');
        }
    })
    .catch(error => {
        hideTerminalLoading();
        addTerminalLine('❌ Error:', 'Failed to execute command: ' + error.message, 'error');
        console.error('Command execution error:', error);
    });
}

/**
 * Add a line to the terminal output
 */
function addTerminalLine(prompt, text, type = 'text') {
    const terminalOutput = document.getElementById('terminalOutput');
    const line = document.createElement('div');
    line.className = 'terminal-line fade-in';
    
    const promptSpan = document.createElement('span');
    promptSpan.className = 'prompt';
    promptSpan.textContent = prompt;
    
    const textSpan = document.createElement('span');
    textSpan.className = `text text-${type}`;
    
    // Handle different text types
    if (type === 'command') {
        textSpan.style.color = '#58a6ff';
        textSpan.style.fontWeight = 'bold';
    } else if (type === 'error') {
        textSpan.style.color = '#f85149';
    } else if (type === 'output') {
        textSpan.style.color = '#c9d1d9';
    }
    
    textSpan.textContent = text;
    
    line.appendChild(promptSpan);
    line.appendChild(textSpan);
    terminalOutput.appendChild(line);
    
    // Auto-scroll to bottom
    if (document.getElementById('autoScroll').checked) {
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    }
    
    // Keep only last 100 lines
    const lines = terminalOutput.querySelectorAll('.terminal-line');
    if (lines.length > 100) {
        lines[0].remove();
    }
}

/**
 * Show terminal loading state
 */
function showTerminalLoading() {
    const loadingLine = document.createElement('div');
    loadingLine.className = 'terminal-line';
    loadingLine.id = 'loadingLine';
    
    const promptSpan = document.createElement('span');
    promptSpan.className = 'prompt';
    promptSpan.textContent = '⏳ Processing...';
    
    const spinnerSpan = document.createElement('span');
    spinnerSpan.className = 'loading-spinner ms-2';
    
    loadingLine.appendChild(promptSpan);
    loadingLine.appendChild(spinnerSpan);
    
    document.getElementById('terminalOutput').appendChild(loadingLine);
}

/**
 * Hide terminal loading state
 */
function hideTerminalLoading() {
    const loadingLine = document.getElementById('loadingLine');
    if (loadingLine) {
        loadingLine.remove();
    }
}

/**
 * Clear terminal output
 */
function clearTerminal() {
    const terminalOutput = document.getElementById('terminalOutput');
    terminalOutput.innerHTML = '';
    
    // Add welcome message
    addTerminalLine('🚀 AI Shell>', 'Terminal cleared. Welcome back!', 'text');
}

/**
 * Download terminal history
 */
function downloadHistory() {
    const history = terminalHistory.map(item => 
        `[${item.timestamp}] ${item.command}\nOutput: ${item.output}\nError: ${item.error}\n---\n`
    ).join('\n');
    
    const blob = new Blob([history], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `terminal_history_${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
}

/**
 * Load terminal history from server
 */
function loadTerminalHistory() {
    fetch('/api/terminal/history')
        .then(response => response.json())
        .then(data => {
            terminalHistory = data;
            console.log('📚 Terminal history loaded:', data.length, 'commands');
        })
        .catch(error => {
            console.error('Failed to load terminal history:', error);
        });
}

/**
 * Toggle voice recognition
 */
function toggleVoiceRecognition() {
    if (isRecording) {
        stopVoiceRecognition();
    } else {
        startVoiceRecognition();
    }
}

/**
 * Start voice recognition
 */
function startVoiceRecognition() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showNotification('Voice recognition not supported in this browser', 'warning');
        return;
    }
    
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            isRecording = true;
            isListening = true;
            
            // Update UI
            const voiceBtn = document.getElementById('voiceBtn');
            voiceBtn.classList.add('listening');
            voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
            
            // Show status
            document.getElementById('voiceStatus').classList.remove('d-none');
            document.getElementById('voiceStatusText').textContent = 'Listening... Speak now!';
            
            // Start recording
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };
            
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                transcribeAudio(audioBlob);
                
                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
            };
            
            mediaRecorder.start();
            
            // Auto-stop after 10 seconds
            setTimeout(() => {
                if (isRecording) {
                    stopVoiceRecognition();
                }
            }, 10000);
            
        })
        .catch(error => {
            console.error('Voice recognition error:', error);
            showNotification('Failed to start voice recognition: ' + error.message, 'danger');
        });
}

/**
 * Stop voice recognition
 */
function stopVoiceRecognition() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        isListening = false;
        
        // Update UI
        const voiceBtn = document.getElementById('voiceBtn');
        voiceBtn.classList.remove('listening');
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        
        // Hide status
        document.getElementById('voiceStatus').classList.add('d-none');
    }
}

/**
 * Transcribe audio and convert to text
 */
function transcribeAudio(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob);
    
    fetch('/api/voice/transcribe', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show transcription
            document.getElementById('transcribedText').value = data.transcription;
            document.getElementById('voiceTranscription').classList.remove('d-none');
            
            showNotification('Voice transcribed successfully!', 'success');
        } else {
            showNotification('Failed to transcribe audio: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('Transcription error:', error);
        showNotification('Failed to transcribe audio', 'danger');
    });
}

/**
 * Execute voice command
 */
function executeVoiceCommand() {
    const transcription = document.getElementById('transcribedText').value.trim();
    
    if (transcription) {
        // Send voice command via WebSocket
        if (socket) {
            socket.emit('voice_command', { command: transcription });
        }
        
        // Hide transcription panel
        document.getElementById('voiceTranscription').classList.add('d-none');
        
        // Add to terminal
        addTerminalLine('🎤 Voice Command:', transcription, 'command');
        
        showNotification('Voice command sent for execution', 'info');
    }
}

/**
 * Handle voice command result
 */
function handleVoiceCommandResult(data) {
    if (data.output) {
        addTerminalLine('📤 Voice Output:', data.output, 'output');
    }
    if (data.error) {
        addTerminalLine('❌ Voice Error:', data.error, 'error');
    }
}

/**
 * Send AI message
 */
function sendAIMessage() {
    const messageInput = document.getElementById('aiMessage');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Show loading state
    const aiResponse = document.getElementById('aiResponse');
    const aiResponseText = document.getElementById('aiResponseText');
    aiResponse.classList.remove('d-none');
    aiResponseText.innerHTML = '<div class="loading-spinner"></div> Processing...';
    
    // Send to AI
    fetch('/api/ai/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            aiResponseText.innerHTML = `
                <div class="mb-2">
                    <small class="text-muted">Model: ${data.model}</small>
                </div>
                <div>${data.response}</div>
            `;
        } else {
            aiResponseText.innerHTML = `<div class="text-danger">Error: ${data.error}</div>`;
        }
    })
    .catch(error => {
        aiResponseText.innerHTML = `<div class="text-danger">Failed to get AI response: ${error.message}</div>`;
        console.error('AI chat error:', error);
    });
    
    // Clear input
    messageInput.value = '';
}

/**
 * List files in current directory
 */
function listFiles() {
    const path = document.getElementById('filePath').value;
    currentPath = path;
    
    fetch(`/api/files/list?path=${encodeURIComponent(path)}`)
        .then(response => response.json())
        .then(data => {
            displayFileList(data);
        })
        .catch(error => {
            console.error('Failed to list files:', error);
            showNotification('Failed to list files', 'danger');
        });
}

/**
 * Display file list
 */
function displayFileList(files) {
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = '';
    
    if (files.length === 0) {
        fileList.innerHTML = '<div class="text-muted text-center py-3">No files found</div>';
        return;
    }
    
    files.forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = `file-item ${file.is_dir ? 'directory' : 'file'} cursor-pointer`;
        fileItem.onclick = () => handleFileClick(file);
        
        const icon = document.createElement('span');
        icon.className = 'file-icon';
        icon.innerHTML = file.is_dir ? '📁' : getFileIcon(file.name);
        
        const name = document.createElement('span');
        name.className = 'file-name text-truncate';
        name.textContent = file.name;
        name.title = file.name;
        
        const size = document.createElement('span');
        size.className = 'file-size';
        size.textContent = file.is_dir ? '' : formatFileSize(file.size);
        
        fileItem.appendChild(icon);
        fileItem.appendChild(name);
        fileItem.appendChild(size);
        
        fileList.appendChild(fileItem);
    });
}

/**
 * Handle file click
 */
function handleFileClick(file) {
    if (file.is_dir) {
        // Navigate to directory
        document.getElementById('filePath').value = file.path;
        listFiles();
    } else {
        // Open file viewer
        openFileViewer(file);
    }
}

/**
 * Open file viewer modal
 */
function openFileViewer(file) {
    fetch(`/api/files/read?path=${encodeURIComponent(file.path)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('filePathDisplay').value = file.path;
                document.getElementById('fileContent').value = data.content;
                
                // Show modal
                const modal = new bootstrap.Modal(document.getElementById('fileViewerModal'));
                modal.show();
            } else {
                showNotification('Failed to read file: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            console.error('File read error:', error);
            showNotification('Failed to read file', 'danger');
        });
}

/**
 * Edit file content
 */
function editFile() {
    const filePath = document.getElementById('filePathDisplay').value;
    const content = document.getElementById('fileContent').value;
    
    fetch('/api/files/write', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path: filePath, content: content })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('File saved successfully!', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('fileViewerModal'));
            modal.hide();
            
            // Refresh file list
            listFiles();
        } else {
            showNotification('Failed to save file: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('File write error:', error);
        showNotification('Failed to save file', 'danger');
    });
}

/**
 * Update system status from API
 */
function updateSystemStatusFromAPI() {
    fetch('/api/system/status')
        .then(response => response.json())
        .then(data => {
            updateSystemStatus(data);
        })
        .catch(error => {
            console.error('Failed to get system status:', error);
        });
}

/**
 * Update system status display
 */
function updateSystemStatus(data) {
    // Update progress bars
    document.getElementById('cpuProgress').style.width = data.cpu.percent + '%';
    document.getElementById('cpuProgress').textContent = Math.round(data.cpu.percent) + '%';
    
    document.getElementById('memoryProgress').style.width = data.memory.percent + '%';
    document.getElementById('memoryProgress').textContent = Math.round(data.memory.percent) + '%';
    
    // Update disk usage if available
    if (data.disk) {
        document.getElementById('diskProgress').style.width = data.disk.percent + '%';
        document.getElementById('diskProgress').textContent = Math.round(data.disk.percent) + '%';
    }
    
    // Update timestamp
    document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
    
    // Update progress bar colors based on usage
    updateProgressBarColors();
}

/**
 * Update progress bar colors based on usage
 */
function updateProgressBarColors() {
    const progressBars = document.querySelectorAll('.progress-bar');
    
    progressBars.forEach(bar => {
        const width = parseInt(bar.style.width);
        if (width > 80) {
            bar.className = 'progress-bar bg-danger';
        } else if (width > 60) {
            bar.className = 'progress-bar bg-warning';
        } else if (width > 40) {
            bar.className = 'progress-bar bg-info';
        } else {
            bar.className = 'progress-bar bg-success';
        }
    });
}

/**
 * Get network information
 */
function getNetworkInfo() {
    // Get local IP (this is a simplified approach)
    fetch('https://api.ipify.org?format=json')
        .then(response => response.json())
        .then(data => {
            document.getElementById('externalIP').textContent = data.ip;
        })
        .catch(error => {
            document.getElementById('externalIP').textContent = 'Unable to get';
        });
    
    // Local IP would typically come from server
    document.getElementById('localIP').textContent = window.location.hostname;
}

/**
 * Refresh process list
 */
function refreshProcesses() {
    // This would typically call an API endpoint
    // For now, we'll show a placeholder
    const processList = document.getElementById('processList');
    processList.innerHTML = '<div class="text-muted text-center py-2">Process monitoring coming soon</div>';
}

/**
 * Show system status details
 */
function showSystemStatus() {
    updateSystemStatusFromAPI();
    showNotification('System status updated', 'info');
}

/**
 * Show settings modal
 */
function showSettings() {
    const modal = new bootstrap.Modal(document.getElementById('settingsModal'));
    modal.show();
}

/**
 * Save settings
 */
function saveSettings() {
    const theme = document.getElementById('terminalTheme').value;
    const refreshInterval = document.getElementById('refreshInterval').value;
    const autoScroll = document.getElementById('autoScroll').checked;
    
    // Save to localStorage
    localStorage.setItem('terminalTheme', theme);
    localStorage.setItem('refreshInterval', refreshInterval);
    localStorage.setItem('autoScroll', autoScroll);
    
    // Apply theme
    applyTerminalTheme(theme);
    
    // Update refresh interval
    if (window.systemMonitoringInterval) {
        clearInterval(window.systemMonitoringInterval);
        window.systemMonitoringInterval = setInterval(updateSystemStatusFromAPI, refreshInterval * 1000);
    }
    
    showNotification('Settings saved successfully!', 'success');
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
    modal.hide();
}

/**
 * Load saved settings
 */
function loadSettings() {
    const theme = localStorage.getItem('terminalTheme') || 'dark';
    const refreshInterval = localStorage.getItem('refreshInterval') || '5';
    const autoScroll = localStorage.getItem('autoScroll') !== 'false';
    
    document.getElementById('terminalTheme').value = theme;
    document.getElementById('refreshInterval').value = refreshInterval;
    document.getElementById('autoScroll').checked = autoScroll;
    
    applyTerminalTheme(theme);
}

/**
 * Apply terminal theme
 */
function applyTerminalTheme(theme) {
    const terminal = document.getElementById('terminalOutput');
    terminal.className = `terminal-window p-3 terminal-theme-${theme}`;
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

/**
 * Get file icon based on extension
 */
function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const iconMap = {
        'py': '🐍',
        'js': '📜',
        'html': '🌐',
        'css': '🎨',
        'json': '📋',
        'md': '📝',
        'txt': '📄',
        'sh': '⚡',
        'py': '🐍',
        'js': '📜',
        'html': '🌐',
        'css': '🎨',
        'json': '📋',
        'md': '📝',
        'txt': '📄',
        'sh': '⚡'
    };
    
    return iconMap[ext] || '📄';
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Handle page visibility change
 */
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden, pause heavy operations
        console.log('Page hidden, pausing heavy operations');
    } else {
        // Page is visible, resume operations
        console.log('Page visible, resuming operations');
        updateSystemStatusFromAPI();
    }
});

/**
 * Handle beforeunload event
 */
window.addEventListener('beforeunload', function() {
    // Clean up WebSocket connection
    if (socket) {
        socket.disconnect();
    }
    
    // Stop voice recording if active
    if (isRecording) {
        stopVoiceRecognition();
    }
});

// Export functions for global access
window.executeCommand = executeCommand;
window.executeCommandFromInput = executeCommandFromInput;
window.clearTerminal = clearTerminal;
window.downloadHistory = downloadHistory;
window.toggleVoiceRecognition = toggleVoiceRecognition;
window.executeVoiceCommand = executeVoiceCommand;
window.sendAIMessage = sendAIMessage;
window.listFiles = listFiles;
window.openFileViewer = openFileViewer;
window.editFile = editFile;
window.showSystemStatus = showSystemStatus;
window.refreshProcesses = refreshProcesses;
window.showSettings = showSettings;
window.saveSettings = saveSettings;

console.log('🚀 Dashboard JavaScript loaded successfully!');