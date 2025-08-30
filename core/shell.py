# core/shell.py
import sys
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Import all core components from the package
from .ai_manager import AIManager
from .system_controller import SystemController
from .task_manager import TaskManager
from .learning_system import LearningSystem
from .automation import AutomationEngine

# Import modular components
from modules.website_generator import WebsiteGenerator
from modules.code_generator import CodeGenerator

# Setup a rich console for beautiful output
console = Console()

class AIShell:
    """
    The main class that orchestrates the entire AI-powered shell.
    It initializes all subsystems and manages the main run loop.
    """
    def __init__(self, config_manager):
        self.config = config_manager
        self.is_running = True
        self.history = [] # Simple session history
        self.conversation_history = [] # Full conversation context for AI
        self.terminal_mode = False # Full terminal control mode
        self.auto_execute_enabled = True # Auto-execution for terminal commands

        # --- Initialize Core Components ---
        self.ai_manager = AIManager(self.config)
        self.system_controller = SystemController()
        self.task_manager = TaskManager()
        
        # Initialize the learning system with a dedicated database file
        data_dir = Path.cwd() / "data"
        self.learning_system = LearningSystem(db_path=data_dir / "learning.db")
        
        # Initialize the automation engine, giving it access to other controllers
        self.automation_engine = AutomationEngine(self.system_controller, self.ai_manager)

        # --- Initialize Modular Components ---
        self.website_generator = WebsiteGenerator(self.ai_manager, console)
        self.code_generator = CodeGenerator(self.ai_manager, console)
        
    def print_welcome_message(self):
        """Prints a rich, styled welcome message when the shell starts."""
        welcome_text = Text.assemble(
            ("Welcome to the ", "default"),
            ("Unified AI Shell v5.0", "bold magenta"),
            ("\nType '/help' for a list of commands or just start chatting!", "cyan")
        )
        console.print(Panel(welcome_text, title="🤖 AI Shell", border_style="green", expand=False))

    def run(self):
        """The main execution loop for the shell."""
        self.print_welcome_message()
        self.automation_engine.start_monitoring() # Start background task scheduler

        while self.is_running:
            try:
                # The prompt indicates the current mode
                if self.terminal_mode:
                    prompt_style = "bold red"
                    prompt_char = "💀"
                    prompt_text = "TERMINAL"
                elif self.automation_engine.auto_execute_enabled:
                    prompt_style = "bold green"
                    prompt_char = "🚀"
                    prompt_text = "AI Shell"
                else:
                    prompt_style = "bold yellow"
                    prompt_char = "▶"
                    prompt_text = "AI Shell"
                
                user_input = console.input(f"[{prompt_style}]{prompt_char} {prompt_text}> [/]")

                # Clean up control characters and arrow key inputs
                user_input = ''.join(char for char in user_input if char.isprintable() and ord(char) >= 32)
                
                if not user_input.strip():
                    continue

                self.history.append(user_input)

                # Handle terminal mode
                if self.terminal_mode:
                    self._handle_terminal_input(user_input)
                    continue

                # First, check if the input is a special command (e.g., /help)
                if self._handle_special_commands(user_input):
                    continue

                # Check if the command should be auto-executed by the automation engine
                if self.automation_engine._should_auto_execute(user_input):
                    self.automation_engine.handle_auto_execution(user_input, self)
                    continue

                # If not a special command or auto-executed, treat as a prompt for the AI
                start_time = time.time()
                task_type = self.ai_manager.classify_task(user_input)
                
                # Add user input to conversation history
                self.conversation_history.append({"role": "user", "content": user_input})
                
                # Let the AI Manager coordinate the response with conversation context
                ai_response, model_used = self.ai_manager.get_response_with_context(user_input, self.conversation_history, task_type)
                
                # Add AI response to conversation history
                self.conversation_history.append({"role": "assistant", "content": ai_response})
                
                response_time = time.time() - start_time
                
                # Display the response and record the interaction for learning
                self.ai_manager.display_response(ai_response, model_used, response_time)
                self.learning_system.record_interaction(user_input, ai_response, model_used, task_type, response_time, was_successful=True)

            except KeyboardInterrupt:
                console.print("\n[bold yellow]Type '/exit' to quit. Press Ctrl+C again to force exit.[/bold yellow]")
            except Exception as e:
                console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")
                # Only record interaction if user_input is defined
                if 'user_input' in locals():
                    self.learning_system.record_interaction(user_input, str(e), "Error", "unknown", 0, was_successful=False, error_message=str(e))

    def _handle_special_commands(self, user_input: str) -> bool:
        """
        Handles internal commands that start with '/'.
        Returns True if the input was a special command, False otherwise.
        """
        command = user_input.strip().lower()

        if command == "/exit":
            self.is_running = False
            self.automation_engine.stop_monitoring()
            console.print("[bold cyan]Goodbye![/bold cyan]")
            return True
        
        if command == "/help":
            self._print_help()
            return True

        if command == "/status":
            self.system_controller.execute_command("status")
            return True
            
        if command == "/auto":
            self.automation_engine.auto_execute_enabled = True
            console.print("[green]Auto-execution enabled.[/green]")
            return True

        if command == "/noauto":
            self.automation_engine.auto_execute_enabled = False
            console.print("[yellow]Auto-execution disabled.[/yellow]")
            return True

        if command == "/report":
            console.print(self.learning_system.get_performance_report())
            return True
            
        if command == "/clear":
            self.conversation_history = []
            console.print("[green]Conversation history cleared.[/green]")
            return True
            
        if command == "/context":
            self._show_conversation_context()
            return True
            
        if command == "/create_file":
            self._create_file_from_context()
            return True
            
        if command == "/terminal":
            self._enable_terminal_mode()
            return True
            
        if command == "/safe":
            self._disable_terminal_mode()
            return True
            
        if command.startswith("/read "):
            filepath = command[6:].strip()
            self._read_file_command(filepath)
            return True
            
        if command.startswith("/write "):
            # Use a more robust parsing approach
            import shlex
            try:
                parts = shlex.split(command[7:])  # Remove "/write " and split
                if len(parts) >= 2:
                    filepath = parts[0]
                    content = " ".join(parts[1:])  # Join remaining parts as content
                    self._write_file_command(filepath, content)
                else:
                    console.print("[red]Usage: /write <filepath> <content>[/red]")
            except Exception as e:
                console.print(f"[red]Error parsing command: {e}[/red]")
            return True
            
        if command.startswith("/append "):
            # Use a more robust parsing approach
            import shlex
            try:
                parts = shlex.split(command[8:])  # Remove "/append " and split
                if len(parts) >= 2:
                    filepath = parts[0]
                    content = " ".join(parts[1:])  # Join remaining parts as content
                    self._append_file_command(filepath, content)
                else:
                    console.print("[red]Usage: /append <filepath> <content>[/red]")
            except Exception as e:
                console.print(f"[red]Error parsing command: {e}[/red]")
            return True
            
        if command.startswith("/list"):
            path = command[6:].strip() if len(command) > 6 else "."
            self._list_directory_command(path)
            return True
            
        if command.startswith("/info "):
            filepath = command[6:].strip()
            self._file_info_command(filepath)
            return True
            
        if command == "/health":
            self._check_api_health()
            return True
            
        if command == "/create_website":
            self._create_website_and_run()
            return True
            
        if command == "/create_gui":
            self._create_gui_application()
            return True
            
        if command == "/stop_servers":
            self._stop_running_servers()
            return True
            
        if command == "/launch_gui":
            self._launch_gui_application()
            return True
            
        return False

    def _print_help(self):
        """Print help information for available commands."""
        help_text = """
[bold cyan]🚀 Unified AI Shell - Available Commands[/bold cyan]

[bold green]Core Commands:[/bold green]
  /help                    - Show this help message
  /clear                   - Clear terminal
  /context                 - Show conversation context
  /health                  - Check API health status
  /terminal                - Enable full terminal mode
  /safe                    - Disable terminal mode

[bold green]File Operations:[/bold green]
  /read <filepath>         - Read file contents
  /write <filepath> <content> - Write content to file
  /append <filepath> <content> - Append content to file
  /list [directory]        - List directory contents
  /info <filepath>         - Get file information
  /create_file             - Create file from conversation context

[bold green]Web Development:[/bold green]
  /create_website          - Generate and host a website
  /stop_servers            - Stop running web servers

[bold green]GUI Applications:[/bold green]
  /create_gui              - Generate Python GUI application
  /launch_gui              - Launch GUI application

[bold green]🤖 AI Agents & Code Analysis:[/bold green]
  /ai_agent <action>       - Manage AI agents (create, start, stop, list)
  /code_review <file>      - AI-powered code review and suggestions
  /bug_finder <file>       - Static analysis and bug detection
  /performance_analyzer <file> - Code performance optimization
  /security_scanner <file> - Security vulnerability detection

[bold green]🔧 DevOps & Infrastructure:[/bold green]
  /ci_cd <action>          - Set up CI/CD pipelines (GitHub Actions, GitLab CI)
  /monitoring <action>     - Application monitoring setup
  /logging <action>        - Centralized logging systems
  /backup_system <action>  - Automated backup solutions
  /load_testing <target>   - Performance testing tools

[bold green]📊 Data Science & Analytics:[/bold green]
  /data_visualization <data> - Create charts and dashboards
  /etl_pipeline <source>   - Data processing pipelines
  /api_analytics <endpoint> - API usage analytics
  /predictive_models <data> - Machine learning models

[bold green]📚 Documentation & Learning:[/bold green]
  /generate_docs <project> - Auto-generate documentation
  /create_tutorial <topic> - Interactive tutorials
  /code_examples <language> - Example code repository
  /api_docs <api>          - OpenAPI/Swagger documentation
  /user_manual <tool>      - User guides and manuals

[bold green]🎨 UI/UX & Customization:[/bold green]
  /theme_switcher <theme>  - Switch between themes (dark/light)
  /custom_commands <action> - Manage custom commands
  /shortcuts <action>      - Keyboard shortcuts
  /plugins <action>        - Plugin system management
  /dashboard               - Web-based management interface

[bold green]🔍 Advanced File Operations:[/bold green]
  /search_files <query>    - Full-text file search
  /file_converter <file>   - Convert between file formats
  /batch_processor <action> - Process multiple files
  /file_encryption <file>  - Encrypt/decrypt files
  /file_sync <source> <dest> - Sync files across directories

[bold green]🌐 Website Cloning:[/bold green]
  /clone_website <url>     - Clone full website with all content
  /quick_clone <url>       - Quick website clone (limited depth)
  /full_clone <url>        - Full website clone (maximum depth)
  /list_cloned_sites       - List all cloned websites

[bold cyan]Examples:[/bold cyan]
  /ai_agent create code_reviewer "Security Auditor"
  /code_review core/shell.py
  /clone_website https://example.com
  /data_visualization sample_sales.csv
  /ci_cd setup github

[bold yellow]Note:[/bold yellow] Some commands require additional setup or dependencies.
Type /help <command> for detailed help on specific commands.
"""
        console.print(help_text)
    
    def _show_conversation_context(self):
        """Shows the current conversation context to help users understand what the AI remembers."""
        if not self.conversation_history:
            console.print("[yellow]No conversation history yet.[/yellow]")
            return
        
        console.print("[bold cyan]Current Conversation Context:[/bold cyan]")
        console.print("[dim]Last 5 conversation turns:[/dim]")
        
        # Show last 5 turns
        recent_history = self.conversation_history[-10:]  # Get last 10 items (5 turns)
        
        for i, turn in enumerate(recent_history):
            role = turn["role"]
            content = turn["content"][:100] + "..." if len(turn["content"]) > 100 else turn["content"]
            
            if role == "user":
                console.print(f"[green]User:[/green] {content}")
            elif role == "assistant":
                console.print(f"[blue]Assistant:[/blue] {content}")
        
        console.print(f"\n[dim]Total conversation turns: {len(self.conversation_history) // 2}[/dim]")
    
    def _create_file_from_context(self):
        """Creates a file based on the last AI response that contains code."""
        if not self.conversation_history:
            console.print("[yellow]No conversation history to create file from.[/yellow]")
            return
        
        # Find the last AI response that might contain code
        for i in range(len(self.conversation_history) - 1, -1, -1):
            turn = self.conversation_history[i]
            if turn["role"] == "assistant":
                content = turn["content"]
                # Look for code blocks
                if "```python" in content or "```" in content:
                    # Extract the code
                    code = self._extract_code_from_response(content)
                    if code:
                        filename = self._suggest_filename(code)
                        self._save_code_to_file(filename, code)
                        return
        
        console.print("[yellow]No code found in recent conversation to save.[/yellow]")
    
    def _extract_code_from_response(self, response: str) -> str:
        """Extract Python code from AI response."""
        import re
        
        # Look for Python code blocks
        python_pattern = r'```python\s*\n(.*?)\n```'
        python_matches = re.findall(python_pattern, response, re.DOTALL)
        
        if python_matches:
            return python_matches[0].strip()
        
        # Look for generic code blocks
        code_pattern = r'```\s*\n(.*?)\n```'
        code_matches = re.findall(code_pattern, response, re.DOTALL)
        
        if code_matches:
            return code_matches[0].strip()
        
        return ""
    
    def _suggest_filename(self, code: str) -> str:
        """Suggest a filename based on the code content."""
        # Look for common patterns in the code
        if "def is_prime" in code or "def sieve" in code or "prime" in code.lower():
            return "prime_utils.py"
        elif "def fibonacci" in code or "fibonacci" in code.lower():
            return "fibonacci.py"
        elif "def factorial" in code or "factorial" in code.lower():
            return "factorial.py"
        elif "class" in code and "def __init__" in code:
            return "my_class.py"
        elif "import flask" in code or "from flask" in code:
            return "app.py"
        elif "import requests" in code:
            return "web_scraper.py"
        else:
            return "generated_code.py"
    
    def _save_code_to_file(self, filename: str, code: str):
        """Save code to a file with user confirmation."""
        try:
            # Create generated_code directory if it doesn't exist
            import os
            os.makedirs("generated_code", exist_ok=True)
            
            filepath = os.path.join("generated_code", filename)
            
            # Check if file already exists
            if os.path.exists(filepath):
                console.print(f"[yellow]File {filepath} already exists. Overwrite? (y/n):[/yellow]")
                response = input().lower().strip()
                if response != 'y':
                    console.print("[yellow]File creation cancelled.[/yellow]")
                    return
            
            # Write the code to file
            with open(filepath, 'w') as f:
                f.write(code)
            
            console.print(f"[green]✓ Code saved to {filepath}[/green]")
            console.print(f"[dim]File size: {len(code)} characters[/dim]")
            
            # Show a preview
            lines = code.split('\n')
            if len(lines) > 10:
                preview = '\n'.join(lines[:10]) + '\n...'
            else:
                preview = code
            
            console.print(f"\n[bold cyan]Preview:[/bold cyan]")
            console.print(f"[dim]{preview}[/dim]")
            
        except Exception as e:
            console.print(f"[bold red]Error saving file: {e}[/bold red]")
    
    def _enable_terminal_mode(self):
        """Enables full terminal control mode."""
        self.terminal_mode = True
        self.auto_execute_enabled = True
        console.print("[bold red]🚨 TERMINAL MODE ENABLED - FULL SYSTEM ACCESS[/bold red]")
        console.print("[red]The AI can now execute any command on your system.[/red]")
        console.print("[yellow]Type '/safe' to disable terminal mode.[/yellow]")
        console.print("[dim]Use with caution - this gives full system access.[/dim]")
    
    def _disable_terminal_mode(self):
        """Disables terminal control mode."""
        self.terminal_mode = False
        self.auto_execute_enabled = False
        console.print("[green]✓ Terminal mode disabled. System is now safe.[/green]")
        console.print("[dim]Auto-execution is now disabled.[/dim]")
    
    def _execute_terminal_command(self, command: str) -> tuple[str, int]:
        """Execute a terminal command and return output and exit code."""
        import subprocess
        
        try:
            # Execute the command using shell=True for shell features like redirection
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            return result.stdout, result.returncode
            
        except subprocess.TimeoutExpired:
            return "Command timed out after 30 seconds.", 1
        except FileNotFoundError:
            return f"Command not found: {command}", 1
        except Exception as e:
            return f"Error executing command: {e}", 1
    
    def _handle_terminal_input(self, user_input: str):
        """Handle input in terminal mode."""
        if user_input.strip().lower() in ['exit', 'quit', '/exit', '/quit']:
            self.is_running = False
            return
        
        if user_input.strip().lower() == '/safe':
            self._disable_terminal_mode()
            return
        
        # Execute the command
        console.print(f"[bold cyan]Executing: {user_input}[/bold cyan]")
        output, exit_code = self._execute_terminal_command(user_input)
        
        if exit_code == 0:
            console.print(f"[green]Output:[/green]")
            console.print(output)
        else:
            console.print(f"[red]Error (exit code {exit_code}):[/red]")
            console.print(output)
        
        console.print(f"[dim]Exit code: {exit_code}[/dim]\n")
    
    def _read_file_command(self, filepath: str):
        """Handle /read command."""
        content = self.ai_manager.read_file(filepath)
        console.print(f"[bold cyan]File contents of '{filepath}':[/bold cyan]")
        console.print(f"[green]{content}[/green]")
    
    def _write_file_command(self, filepath: str, content: str):
        """Handle /write command."""
        result = self.ai_manager.write_file(filepath, content)
        console.print(f"[bold cyan]Write result:[/bold cyan] {result}")
    
    def _append_file_command(self, filepath: str, content: str):
        """Handle /append command."""
        result = self.ai_manager.append_file(filepath, content)
        console.print(f"[bold cyan]Append result:[/bold cyan] {result}")
    
    def _list_directory_command(self, path: str):
        """Handle /list command."""
        listing = self.ai_manager.list_directory(path)
        console.print(f"[bold cyan]Directory listing:[/bold cyan]")
        console.print(f"[green]{listing}[/green]")
    
    def _file_info_command(self, filepath: str):
        """Handle /info command."""
        info = self.ai_manager.get_file_info(filepath)
        console.print(f"[bold cyan]File information:[/bold cyan]")
        console.print(f"[green]{info}[/green]")
    
    def _check_api_health(self):
        """Handle /health command."""
        health_status = self.ai_manager.check_api_health()
        console.print(f"[bold cyan]API Health Status:[/bold cyan]")
        
        for api, status in health_status.items():
            if status['status'] == 'healthy':
                console.print(f"[green]✓ {api.upper()}: Healthy[/green]")
            elif status['status'] == 'error':
                console.print(f"[red]✗ {api.upper()}: Error - {status['error']}[/red]")
            else:
                console.print(f"[yellow]? {api.upper()}: Unknown[/yellow]")
    
    def _create_website_and_run(self):
        """Create a complete website and run it on localhost."""
        import os
        import subprocess
        import sys
        import time
        
        website_dir = "my_website"
        static_dir = os.path.join(website_dir, "static")
        
        # Create directories
        os.makedirs(website_dir, exist_ok=True)
        os.makedirs(static_dir, exist_ok=True)
        
        console.print(f"[bold cyan]Creating website in '{website_dir}' directory...[/bold cyan]")
        
        # Create index.html
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>My Local Site</title>
    <link rel="stylesheet" href="static/style.css">
</head>
<body>
    <h1>Welcome to My Local Site</h1>
    <p>This page is served by a Python server running on your machine.</p>

    <button id="clickMe">Click me</button>
    <p id="output"></p>

    <script src="static/script.js"></script>
</body>
</html>"""
        
        # Create style.css
        css_content = """body {
    font-family: Arial, Helvetica, sans-serif;
    background: #f0f8ff;
    margin: 2rem;
    color: #333;
}

h1 {
    color: #0066cc;
}

button {
    padding: .5rem 1rem;
    font-size: 1rem;
    background: #0066cc;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

button:hover {
    background: #0052a3;
}"""
        
        # Create script.js
        js_content = """document.getElementById('clickMe').addEventListener('click', () => {
    const output = document.getElementById('output');
    const now = new Date().toLocaleTimeString();
    output.textContent = `Button clicked at ${now}`;
});"""
        
        # Create server.py
        server_content = """from flask import Flask, send_from_directory
import pathlib

app = Flask(__name__, static_folder='static', static_url_path='/static')

@app.route('/')
def index():
    html_path = pathlib.Path(__file__).parent / 'index.html'
    return html_path.read_text(encoding='utf-8')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)"""
        
        # Write all files
        files_to_create = [
            (os.path.join(website_dir, "index.html"), html_content),
            (os.path.join(static_dir, "style.css"), css_content),
            (os.path.join(static_dir, "script.js"), js_content),
            (os.path.join(website_dir, "server.py"), server_content)
        ]
        
        for filepath, content in files_to_create:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            console.print(f"[green]✓ Created: {filepath}[/green]")
        
        console.print(f"\n[bold green]Website created successfully![/bold green]")
        console.print(f"[cyan]Files created in: {os.path.abspath(website_dir)}[/cyan]")
        
        # Try to install Flask if not available
        try:
            import flask
            console.print("[green]✓ Flask is already installed[/green]")
        except ImportError:
            console.print("[yellow]Installing Flask...[/yellow]")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "flask"], 
                             check=True, capture_output=True, text=True)
                console.print("[green]✓ Flask installed successfully[/green]")
            except subprocess.CalledProcessError as e:
                console.print(f"[red]✗ Failed to install Flask: {e}[/red]")
                console.print("[yellow]You can install it manually with: pip install flask[/yellow]")
        
        # Start the server in background
        console.print(f"\n[bold cyan]Starting Flask server in background...[/bold cyan]")
        console.print(f"[cyan]Server will be available at: http://localhost:5000[/cyan]")
        console.print(f"[yellow]Server is running in background. Use '/stop_servers' to stop it.[/yellow]")
        
        # Change to website directory and start server in background
        os.chdir(website_dir)
        try:
            # Start server in background
            process = subprocess.Popen([sys.executable, "server.py"], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     preexec_fn=os.setsid if hasattr(os, 'setsid') else None)
            
            # Give it a moment to start
            import time
            time.sleep(2)
            
            if process.poll() is None:
                console.print(f"[green]✓ Server started successfully (PID: {process.pid})[/green]")
                console.print(f"[cyan]Website is now running at: http://localhost:5000[/cyan]")
                console.print(f"[yellow]Use '/stop_servers' command to stop all running servers[/yellow]")
            else:
                console.print(f"[red]✗ Server failed to start[/red]")
                stdout, stderr = process.communicate()
                if stderr:
                    console.print(f"[red]Error: {stderr.decode()}[/red]")
                    
        except Exception as e:
            console.print(f"[red]✗ Failed to start server: {e}[/red]")
        finally:
            # Return to original directory
            os.chdir("..")
    
    def _create_gui_application(self):
        """Create a Python GUI application with tkinter."""
        import os
        
        gui_dir = "my_gui_app"
        os.makedirs(gui_dir, exist_ok=True)
        
        console.print(f"[bold cyan]Creating GUI application in '{gui_dir}' directory...[/bold cyan]")
        
        # Create main GUI application
        main_app_content = """import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime

class ModernGUIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Python GUI Application")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        
        # Create widgets
        self._create_widgets()
        
        # Load saved data
        self.load_data()
    
    def _create_widgets(self):
        # Title
        title_label = ttk.Label(self.main_frame, text="Modern Python GUI Application", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Input section
        ttk.Label(self.main_frame, text="Enter Text:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.text_entry = ttk.Entry(self.main_frame, width=50)
        self.text_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Add Item", command=self.add_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_items).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Data", command=self.save_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Load File", command=self.load_file).pack(side=tk.LEFT, padx=5)
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(self.main_frame)
        list_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.listbox = tk.Listbox(list_frame, height=15, width=70)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        self.listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(3, weight=1)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Bind double-click to edit
        self.listbox.bind('<Double-1>', self.edit_item)
        
        # Sample data
        self.items = []
    
    def add_item(self):
        text = self.text_entry.get().strip()
        if text:
            timestamp = datetime.now().strftime("%H:%M:%S")
            item = f"[{timestamp}] {text}"
            self.items.append(item)
            self.listbox.insert(tk.END, item)
            self.text_entry.delete(0, tk.END)
            self.status_var.set(f"Added: {text}")
            self.save_data()
        else:
            messagebox.showwarning("Warning", "Please enter some text!")
    
    def clear_items(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all items?"):
            self.items.clear()
            self.listbox.delete(0, tk.END)
            self.status_var.set("All items cleared")
            self.save_data()
    
    def edit_item(self, event):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            old_text = self.items[index]
            
            # Create edit dialog
            edit_window = tk.Toplevel(self.root)
            edit_window.title("Edit Item")
            edit_window.geometry("400x150")
            edit_window.transient(self.root)
            edit_window.grab_set()
            
            ttk.Label(edit_window, text="Edit item:").pack(pady=10)
            edit_entry = ttk.Entry(edit_window, width=50)
            edit_entry.pack(pady=10)
            edit_entry.insert(0, old_text)
            edit_entry.select_range(0, tk.END)
            edit_entry.focus()
            
            def save_edit():
                new_text = edit_entry.get().strip()
                if new_text:
                    self.items[index] = new_text
                    self.listbox.delete(index)
                    self.listbox.insert(index, new_text)
                    self.status_var.set(f"Edited: {new_text}")
                    self.save_data()
                    edit_window.destroy()
                else:
                    messagebox.showwarning("Warning", "Text cannot be empty!")
            
            ttk.Button(edit_window, text="Save", command=save_edit).pack(pady=10)
            edit_entry.bind('<Return>', lambda e: save_edit())
    
    def save_data(self):
        try:
            data = {
                'items': self.items,
                'timestamp': datetime.now().isoformat()
            }
            with open('gui_data.json', 'w') as f:
                json.dump(data, f, indent=2)
            self.status_var.set("Data saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {e}")
    
    def load_data(self):
        try:
            if os.path.exists('gui_data.json'):
                with open('gui_data.json', 'r') as f:
                    data = json.load(f)
                    self.items = data.get('items', [])
                    for item in self.items:
                        self.listbox.insert(tk.END, item)
                self.status_var.set("Data loaded successfully")
        except Exception as e:
            self.status_var.set(f"Failed to load data: {e}")
    
    def load_file(self):
        filename = filedialog.askopenfilename(
            title="Select a text file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    content = f.read().strip()
                    if content:
                        self.text_entry.delete(0, tk.END)
                        self.text_entry.insert(0, content)
                        self.status_var.set(f"Loaded file: {os.path.basename(filename)}")
                    else:
                        messagebox.showinfo("Info", "File is empty")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")

def main():
    root = tk.Tk()
    app = ModernGUIApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
"""
        
        # Create requirements.txt for GUI app
        requirements_content = """# GUI Application Dependencies
# Most dependencies are built-in with Python
        
# Optional: Install these for enhanced GUI experience
# pip install pillow  # For image handling
# pip install customtkinter  # For modern-looking widgets
# pip install tkinter-tooltip  # For tooltips
"""
        
        # Create README
        readme_content = """# Modern Python GUI Application

A feature-rich GUI application built with Python's tkinter library.

## Features

- ✅ Modern interface with ttk widgets
- ✅ Add, edit, and delete items
- ✅ Persistent data storage (JSON)
- ✅ File loading capabilities
- ✅ Status bar and user feedback
- ✅ Responsive layout

## How to Run

1. Make sure you have Python 3.x installed
2. Run the application:
   ```bash
   python main.py
   ```

## Usage

- **Add Item**: Type text and click "Add Item"
- **Edit Item**: Double-click any item in the list
- **Clear All**: Remove all items (with confirmation)
- **Save Data**: Automatically saves to gui_data.json
- **Load File**: Load text from external files

## Customization

- Modify colors and styles in the `_create_widgets` method
- Add new features by extending the class
- Change the window size in the `__init__` method

## Dependencies

- Python 3.x (built-in tkinter)
- No external packages required!

## Screenshots

The app features a clean, modern interface with:
- Input field for adding items
- Scrollable list of items
- Button controls
- Status bar
- File dialog support

Enjoy building with Python GUI! 🐍✨
"""
        
        # Create a simple calculator GUI as well
        calculator_content = """import tkinter as tk
from tkinter import ttk

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Calculator")
        self.root.geometry("300x400")
        self.root.resizable(False, False)
        
        # Calculator display
        self.display_var = tk.StringVar()
        self.display_var.set("0")
        
        self.create_widgets()
        self.current_number = ""
        self.operation = ""
        self.first_number = 0
        self.new_number = True
    
    def create_widgets(self):
        # Display
        display_frame = ttk.Frame(self.root, padding="10")
        display_frame.pack(fill=tk.X)
        
        self.display = ttk.Entry(display_frame, textvariable=self.display_var, 
                                font=('Arial', 20), justify='right', state='readonly')
        self.display.pack(fill=tk.X)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.root, padding="10")
        buttons_frame.pack(fill=tk.BOTH, expand=True)
        
        # Button layout
        buttons = [
            ('C', 0, 0), ('±', 0, 1), ('%', 0, 2), ('÷', 0, 3),
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('×', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('-', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('+', 3, 3),
            ('0', 4, 0, 2), ('.', 4, 2), ('=', 4, 3)
        ]
        
        for button in buttons:
            if len(button) == 4:  # Special case for zero button
                text, row, col, colspan = button
                btn = ttk.Button(buttons_frame, text=text, command=lambda t=text: self.button_click(t))
                btn.grid(row=row, column=col, columnspan=colspan, sticky='nsew', padx=2, pady=2)
            else:
                text, row, col = button
                btn = ttk.Button(buttons_frame, text=text, command=lambda t=text: self.button_click(t))
                btn.grid(row=row, column=col, sticky='nsew', padx=2, pady=2)
        
        # Configure grid weights
        for i in range(5):
            buttons_frame.rowconfigure(i, weight=1)
        for i in range(4):
            buttons_frame.columnconfigure(i, weight=1)
    
    def button_click(self, value):
        if value.isdigit() or value == '.':
            if self.new_number:
                self.display_var.set(value)
                self.new_number = False
            else:
                if value == '.' and '.' in self.display_var.get():
                    return
                self.display_var.set(self.display_var.get() + value)
        elif value == 'C':
            self.clear()
        elif value == '±':
            self.negate()
        elif value == '%':
            self.percentage()
        elif value in ['+', '-', '×', '÷']:
            self.set_operation(value)
        elif value == '=':
            self.calculate()
    
    def clear(self):
        self.display_var.set("0")
        self.current_number = ""
        self.operation = ""
        self.first_number = 0
        self.new_number = True
    
    def negate(self):
        current = float(self.display_var.get())
        self.display_var.set(str(-current))
    
    def percentage(self):
        current = float(self.display_var.get())
        self.display_var.set(str(current / 100))
    
    def set_operation(self, op):
        self.first_number = float(self.display_var.get())
        self.operation = op
        self.new_number = True
    
    def calculate(self):
        if self.operation:
            second_number = float(self.display_var.get())
            if self.operation == '+':
                result = self.first_number + second_number
            elif self.operation == '-':
                result = self.first_number - second_number
            elif self.operation == '×':
                result = self.first_number * second_number
            elif self.operation == '÷':
                if second_number == 0:
                    self.display_var.set("Error")
                    return
                result = self.first_number / second_number
            
            self.display_var.set(str(result))
            self.operation = ""
            self.new_number = True

def main():
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
"""
        
        # Write all files
        files_to_create = [
            (os.path.join(gui_dir, "main.py"), main_app_content),
            (os.path.join(gui_dir, "calculator.py"), calculator_content),
            (os.path.join(gui_dir, "requirements.txt"), requirements_content),
            (os.path.join(gui_dir, "README.md"), readme_content)
        ]
        
        for filepath, content in files_to_create:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            console.print(f"[green]✓ Created: {filepath}[/green]")
        
        console.print(f"\n[bold green]GUI Application created successfully![/bold green]")
        console.print(f"[cyan]Files created in: {os.path.abspath(gui_dir)}[/cyan]")
        console.print(f"\n[bold cyan]Available Applications:[/bold cyan]")
        console.print(f"[green]• main.py - Full-featured GUI app with data persistence[/green]")
        console.print(f"[green]• calculator.py - Simple calculator application[/green]")
        console.print(f"\n[cyan]To run the main app:[/cyan]")
        console.print(f"[yellow]cd {gui_dir} && python main.py[/yellow]")
        console.print(f"\n[cyan]To run the calculator:[/cyan]")
        console.print(f"[yellow]cd {gui_dir} && python calculator.py[/yellow]")
        console.print(f"\n[bold green]No external dependencies required! All built with Python's built-in tkinter.[/bold green]")
    
    def _stop_running_servers(self):
        """Stop any running Flask or Python servers."""
        import subprocess
        import os
        
        console.print(f"[bold cyan]Stopping running servers...[/bold cyan]")
        
        try:
            # Stop Flask servers
            result = subprocess.run(['pkill', '-f', 'server.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                console.print(f"[green]✓ Stopped Flask servers[/green]")
            else:
                console.print(f"[yellow]No Flask servers were running[/yellow]")
            
            # Stop Python HTTP servers
            result = subprocess.run(['pkill', '-f', 'http.server'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                console.print(f"[green]✓ Stopped Python HTTP servers[/green]")
            else:
                console.print(f"[yellow]No Python HTTP servers were running[/yellow]")
                
            # Check for any remaining Python processes on common ports
            ports_to_check = [5000, 8000, 8080, 3000]
            for port in ports_to_check:
                try:
                    result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                          capture_output=True, text=True)
                    if result.stdout.strip():
                        pids = result.stdout.strip().split('\n')
                        for pid in pids:
                            if pid:
                                subprocess.run(['kill', pid], capture_output=True)
                                console.print(f"[green]✓ Stopped process on port {port} (PID: {pid})[/green]")
                except:
                    pass
                    
        except Exception as e:
            console.print(f"[red]Error stopping servers: {e}[/red]")
        
        console.print(f"[bold green]Server cleanup completed![/bold green]")
    
    def _launch_gui_application(self):
        """Launch a GUI application in a separate terminal."""
        import os
        import subprocess
        
        gui_dir = "my_gui_app"
        if not os.path.exists(gui_dir):
            console.print(f"[red]GUI application directory '{gui_dir}' not found.[/red]")
            console.print(f"[yellow]Use '/create_gui' first to create the application.[/yellow]")
            return
        
        console.print(f"[bold cyan]Launching GUI application in separate terminal...[/bold cyan]")
        
        try:
            # Get the absolute path to the main GUI file
            gui_path = os.path.abspath(os.path.join(gui_dir, "main.py"))
            
            # Launch GUI app in a new terminal window (completely separate)
            if os.name == 'nt':  # Windows
                # Use start command to open new terminal
                subprocess.Popen(['start', 'cmd', '/k', 'python', gui_path], 
                               shell=True, cwd=gui_dir)
            else:  # Linux/macOS
                # Use gnome-terminal, xterm, or konsole based on what's available
                terminal_commands = [
                    ['gnome-terminal', '--', 'bash', '-c', f'cd "{gui_dir}" && python3 "{gui_path}" && echo "GUI app closed. Press Enter to close terminal..." && read'],
                    ['xterm', '-e', f'cd "{gui_dir}" && python3 "{gui_path}" && echo "GUI app closed. Press Enter to close terminal..." && read'],
                    ['konsole', '-e', f'bash -c "cd \\"{gui_dir}\\" && python3 \\"{gui_path}\\" && echo \\"GUI app closed. Press Enter to close terminal...\\" && read"'],
                    ['terminator', '-e', f'cd "{gui_dir}" && python3 "{gui_path}" && echo "GUI app closed. Press Enter to close terminal..." && read'],
                    ['alacritty', '-e', f'bash', '-c', f'cd "{gui_dir}" && python3 "{gui_path}" && echo "GUI app closed. Press Enter to close terminal..." && read']
                ]
                
                app_launched = False
                for cmd in terminal_commands:
                    try:
                        # Check if terminal is available
                        result = subprocess.run(['which', cmd[0]], capture_output=True, text=True)
                        if result.returncode == 0:
                            # Launch GUI app in new terminal
                            subprocess.Popen(cmd, cwd=gui_dir)
                            console.print(f"[green]✓ GUI app launched in {cmd[0]} terminal[/green]")
                            app_launched = True
                            break
                    except:
                        continue
                
                if not app_launched:
                    # Fallback: launch in background
                    console.print(f"[yellow]No terminal found, launching GUI app in background...[/yellow]")
                    subprocess.Popen(['python3', gui_path], 
                                   cwd=gui_dir,
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                    console.print(f"[green]✓ GUI app started in background[/green]")
            
            console.print(f"[cyan]GUI application is now running in separate terminal[/cyan]")
            console.print(f"[yellow]The terminal can be closed independently of this shell.[/yellow]")
                    
        except Exception as e:
            console.print(f"[red]✗ Failed to launch GUI app: {e}[/red]")
            console.print(f"[yellow]You can manually run: cd {gui_dir} && python main.py[/yellow]")

    # New Ethical Hacking Command Handlers
    def _handle_ai_agent_command(self, args: str):
        """Handle AI agent commands."""
        if not hasattr(self, 'ai_agent_manager'):
            try:
                from core.ai_agent import AIAgentManager
                self.ai_agent_manager = AIAgentManager(self.ai_manager)
                console.print("[green]✅ AI Agent Manager initialized[/green]")
            except ImportError as e:
                console.print(f"[red]❌ Failed to import AI Agent Manager: {e}[/red]")
                return
        
        if not args:
            console.print("[yellow]Usage: /ai_agent <action> [options][/yellow]")
            console.print("[cyan]Actions: create, start, stop, list, remove[/cyan]")
            return
        
        parts = args.split()
        action = parts[0].lower()
        
        if action == "create":
            if len(parts) < 3:
                console.print("[yellow]Usage: /ai_agent create <type> <name>[/yellow]")
                return
            agent_type = parts[1]
            agent_name = parts[2]
            self.ai_agent_manager.create_agent(agent_name, agent_type)
            
        elif action == "start":
            if len(parts) < 2:
                console.print("[yellow]Usage: /ai_agent start <name>[/yellow]")
                return
            agent_name = parts[1]
            self.ai_agent_manager.start_agent(agent_name)
            
        elif action == "stop":
            if len(parts) < 2:
                console.print("[yellow]Usage: /ai_agent stop <name>[/yellow]")
                return
            agent_name = parts[1]
            self.ai_agent_manager.stop_agent(agent_name)
            
        elif action == "list":
            self.ai_agent_manager.list_agents()
            
        elif action == "remove":
            if len(parts) < 2:
                console.print("[yellow]Usage: /ai_agent remove <name>[/yellow]")
                return
            agent_name = parts[1]
            self.ai_agent_manager.remove_agent(agent_name)
            
        else:
            console.print(f"[yellow]Unknown action: {action}[/yellow]")
    
    def _handle_code_review_command(self, args: str):
        """Handle code review commands."""
        if not args:
            console.print("[yellow]Usage: /code_review <filepath>[/yellow]")
            return
        
        if not hasattr(self, 'code_analyzer'):
            try:
                from core.code_analyzer import CodeAnalyzer
                self.code_analyzer = CodeAnalyzer(self.ai_manager)
                console.print("[green]✅ Code Analyzer initialized[/green]")
            except ImportError as e:
                console.print(f"[red]❌ Failed to import Code Analyzer: {e}[/red]")
                return
        
        file_path = args.strip()
        console.print(f"[cyan]🔍 Analyzing code: {file_path}[/cyan]")
        
        try:
            analysis = self.code_analyzer.analyze_code_file(file_path)
            if 'error' not in analysis:
                report = self.code_analyzer.generate_report(file_path)
                console.print(f"[green]✅ Code analysis completed[/green]")
                
                # Save report to file
                report_file = f"code_review_{Path(file_path).stem}.md"
                Path(report_file).write_text(report)
                console.print(f"[cyan]📋 Report saved: {report_file}[/cyan]")
                
                # Display summary
                bugs = len(analysis.get('bugs', []))
                security_issues = len(analysis.get('security_issues', []))
                performance_issues = len(analysis.get('performance_issues', []))
                
                console.print(f"[cyan]📊 Summary: {bugs} bugs, {security_issues} security issues, {performance_issues} performance issues[/cyan]")
            else:
                console.print(f"[red]❌ Analysis failed: {analysis['error']}[/red]")
                
        except Exception as e:
            console.print(f"[red]❌ Code review failed: {e}[/red]")
    
    def _handle_bug_finder_command(self, args: str):
        """Handle bug finder commands."""
        if not args:
            console.print("[yellow]Usage: /bug_finder <filepath>[/yellow]")
            return
        
        # Use the same code analyzer for bug detection
        self._handle_code_review_command(args)
    
    def _handle_performance_analyzer_command(self, args: str):
        """Handle performance analyzer commands."""
        if not args:
            console.print("[yellow]Usage: /performance_analyzer <filepath>[/yellow]")
            return
        
        # Use the same code analyzer for performance analysis
        self._handle_code_review_command(args)
    
    def _handle_security_scanner_command(self, args: str):
        """Handle security scanner commands."""
        if not args:
            console.print("[yellow]Usage: /security_scanner <filepath>[/yellow]")
            return
        
        # Use the same code analyzer for security scanning
        self._handle_code_review_command(args)
    
    def _handle_ci_cd_command(self, args: str):
        """Handle CI/CD commands."""
        if not hasattr(self, 'devops_tools'):
            try:
                from core.devops_tools import DevOpsTools
                self.devops_tools = DevOpsTools()
                console.print("[green]✅ DevOps Tools initialized[/green]")
            except ImportError as e:
                console.print(f"[red]❌ Failed to import DevOps Tools: {e}[/red]")
                return
        
        if not args:
            console.print("[yellow]Usage: /ci_cd <action>[/yellow]")
            console.print("[cyan]Actions: github, docker, monitoring, logging, backup, load_test[/cyan]")
            return
        
        action = args.strip().lower()
        
        if action == "github":
            self.devops_tools.setup_github_actions()
        elif action == "docker":
            self.devops_tools.setup_docker()
        elif action == "monitoring":
            self.devops_tools.setup_monitoring()
        elif action == "logging":
            self.devops_tools.setup_logging()
        elif action == "backup":
            self.devops_tools.create_backup_system()
        elif action == "load_test":
            self.devops_tools.setup_load_testing()
        elif action == "list":
            self.devops_tools.list_templates()
        else:
            console.print(f"[yellow]Unknown action: {action}[/yellow]")
    
    def _handle_monitoring_command(self, args: str):
        """Handle monitoring commands."""
        self._handle_ci_cd_command("monitoring")
    
    def _handle_logging_command(self, args: str):
        """Handle logging commands."""
        self._handle_ci_cd_command("logging")
    
    def _handle_backup_system_command(self, args: str):
        """Handle backup system commands."""
        self._handle_ci_cd_command("backup")
    
    def _handle_load_testing_command(self, args: str):
        """Handle load testing commands."""
        self._handle_ci_cd_command("load_test")
    
    def _handle_data_visualization_command(self, args: str):
        """Handle data visualization commands."""
        if not hasattr(self, 'data_tools'):
            try:
                from core.data_tools import DataTools
                self.data_tools = DataTools()
                console.print("[green]✅ Data Tools initialized[/green]")
            except ImportError as e:
                console.print(f"[red]❌ Failed to import Data Tools: {e}[/red]")
                return
        
        if not args:
            console.print("[yellow]Usage: /data_visualization <action> [options][/yellow]")
            console.print("[cyan]Actions: create_data, chart, etl, model, dashboard[/cyan]")
            return
        
        parts = args.split()
        action = parts[0].lower()
        
        if action == "create_data":
            data_type = parts[1] if len(parts) > 1 else "sales"
            self.data_tools.create_sample_data(data_type)
            
        elif action == "chart":
            if len(parts) < 3:
                console.print("[yellow]Usage: /data_visualization chart <file> <type>[/yellow]")
                return
            data_file = parts[1]
            chart_type = parts[2]
            self.data_tools.create_visualization(data_file, chart_type)
            
        elif action == "etl":
            if len(parts) < 2:
                console.print("[yellow]Usage: /data_visualization etl <file>[/yellow]")
                return
            source_file = parts[1]
            self.data_tools.create_etl_pipeline(source_file)
            
        elif action == "model":
            if len(parts) < 2:
                console.print("[yellow]Usage: /data_visualization model <file>[/yellow]")
                return
            data_file = parts[1]
            self.data_tools.create_predictive_model(data_file)
            
        elif action == "dashboard":
            self.data_tools.create_dashboard()
            
        elif action == "list":
            self.data_tools.list_datasets()
            
        else:
            console.print(f"[yellow]Unknown action: {action}[/yellow]")
    
    def _handle_etl_pipeline_command(self, args: str):
        """Handle ETL pipeline commands."""
        self._handle_data_visualization_command(f"etl {args}")
    
    def _handle_api_analytics_command(self, args: str):
        """Handle API analytics commands."""
        console.print("[cyan]📊 API Analytics feature coming soon![/cyan]")
    
    def _handle_predictive_models_command(self, args: str):
        """Handle predictive models commands."""
        self._handle_data_visualization_command(f"model {args}")
    
    def _handle_generate_docs_command(self, args: str):
        """Handle documentation generation commands."""
        console.print("[cyan]📚 Documentation generation feature coming soon![/cyan]")
    
    def _handle_create_tutorial_command(self, args: str):
        """Handle tutorial creation commands."""
        console.print("[cyan]🎓 Tutorial creation feature coming soon![/cyan]")
    
    def _handle_code_examples_command(self, args: str):
        """Handle code examples commands."""
        console.print("[cyan]💻 Code examples feature coming soon![/cyan]")
    
    def _handle_api_docs_command(self, args: str):
        """Handle API documentation commands."""
        console.print("[cyan]🔌 API documentation feature coming soon![/cyan]")
    
    def _handle_user_manual_command(self, args: str):
        """Handle user manual commands."""
        console.print("[cyan]📖 User manual feature coming soon![/cyan]")
    
    def _handle_theme_switcher_command(self, args: str):
        """Handle theme switching commands."""
        console.print("[cyan]🎨 Theme switcher feature coming soon![/cyan]")
    
    def _handle_custom_commands_command(self, args: str):
        """Handle custom commands commands."""
        console.print("[cyan]⚙️ Custom commands feature coming soon![/cyan]")
    
    def _handle_shortcuts_command(self, args: str):
        """Handle keyboard shortcuts commands."""
        console.print("[cyan]⌨️ Keyboard shortcuts feature coming soon![/cyan]")
    
    def _handle_plugins_command(self, args: str):
        """Handle plugin system commands."""
        console.print("[cyan]🔌 Plugin system feature coming soon![/cyan]")
    
    def _handle_dashboard_command(self, args: str):
        """Handle dashboard commands."""
        console.print("[cyan]📊 Web dashboard feature coming soon![/cyan]")
    
    def _handle_search_files_command(self, args: str):
        """Handle file search commands."""
        console.print("[cyan]🔍 File search feature coming soon![/cyan]")
    
    def _handle_file_converter_command(self, args: str):
        """Handle file conversion commands."""
        console.print("[cyan]🔄 File converter feature coming soon![/cyan]")
    
    def _handle_batch_processor_command(self, args: str):
        """Handle batch processing commands."""
        console.print("[cyan]📦 Batch processor feature coming soon![/cyan]")
    
    def _handle_file_encryption_command(self, args: str):
        """Handle file encryption commands."""
        console.print("[cyan]🔐 File encryption feature coming soon![/cyan]")
    
    def _handle_file_sync_command(self, args: str):
        """Handle file synchronization commands."""
        console.print("[cyan]🔄 File sync feature coming soon![/cyan]")
    
    # Website Cloning Command Handlers
    def _handle_clone_website_command(self, args: str):
        """Handle website cloning commands."""
        if not args:
            console.print("[yellow]Usage: /clone_website <url> [output_dir][/yellow]")
            return
        
        if not hasattr(self, 'website_cloner'):
            try:
                from core.website_cloner import WebsiteCloner
                self.website_cloner = WebsiteCloner()
                console.print("[green]✅ Website Cloner initialized[/green]")
            except ImportError as e:
                console.print(f"[red]❌ Failed to import Website Cloner: {e}[/red]")
                return
        
        parts = args.split()
        target_url = parts[0]
        output_dir = parts[1] if len(parts) > 1 else None
        
        console.print(f"[cyan]🌐 Starting website clone: {target_url}[/cyan]")
        self.website_cloner.clone_website(target_url, output_dir)
    
    def _handle_quick_clone_command(self, args: str):
        """Handle quick website cloning commands."""
        if not args:
            console.print("[yellow]Usage: /quick_clone <url> [output_dir][/yellow]")
            return
        
        if not hasattr(self, 'website_cloner'):
            try:
                from core.website_cloner import WebsiteCloner
                self.website_cloner = WebsiteCloner()
                console.print("[green]✅ Website Cloner initialized[/green]")
            except ImportError as e:
                console.print(f"[red]❌ Failed to import Website Cloner: {e}[/red]")
                return
        
        parts = args.split()
        target_url = parts[0]
        output_dir = parts[1] if len(parts) > 1 else None
        
        console.print(f"[cyan]⚡ Quick website clone: {target_url}[/cyan]")
        self.website_cloner.quick_clone(target_url, output_dir)
    
    def _handle_full_clone_command(self, args: str):
        """Handle full website cloning commands."""
        if not args:
            console.print("[yellow]Usage: /full_clone <url> [output_dir][/yellow]")
            return
        
        if not hasattr(self, 'website_cloner'):
            try:
                from core.website_cloner import WebsiteCloner
                self.website_cloner = WebsiteCloner()
                console.print("[green]✅ Website Cloner initialized[/green]")
            except ImportError as e:
                console.print(f"[red]❌ Failed to import Website Cloner: {e}[/red]")
                return
        
        parts = args.split()
        target_url = parts[0]
        output_dir = parts[1] if len(parts) > 1 else None
        
        console.print(f"[cyan]🔍 Full website clone: {target_url}[/cyan]")
        self.website_cloner.full_clone(target_url, output_dir)
    
    def _handle_list_cloned_sites_command(self):
        """Handle list cloned sites command."""
        if not hasattr(self, 'website_cloner'):
            try:
                from core.website_cloner import WebsiteCloner
                self.website_cloner = WebsiteCloner()
                console.print("[green]✅ Website Cloner initialized[/green]")
            except ImportError as e:
                console.print(f"[red]❌ Failed to import Website Cloner: {e}[/red]")
                return
        
        self.website_cloner.list_cloned_sites()


