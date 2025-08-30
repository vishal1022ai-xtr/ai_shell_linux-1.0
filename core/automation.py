# core/automation.py
import threading
import time
import schedule
from rich.console import Console

console = Console()

class AutomationEngine:
    """Manages auto-execution, scheduled tasks, and background monitoring."""
    def __init__(self, system_controller, ai_manager):
        self.system_controller = system_controller
        self.ai_manager = ai_manager
        self.auto_execute_enabled = True # Enabled by default for a proactive experience
        self.monitoring_thread = None
        self.is_monitoring = False

    def _should_auto_execute(self, user_input: str) -> bool:
        """
        Intelligently determines if a user's command should be executed automatically.
        This logic is crucial for distinguishing between a command and a question.
        """
        if not self.auto_execute_enabled:
            return False

        input_lower = user_input.lower().strip()
        
        # Clean up any control characters or arrow key inputs
        input_lower = ''.join(char for char in input_lower if char.isprintable() and ord(char) >= 32)
        
        if not input_lower.strip():
            return False

        # Keywords that strongly imply a direct command or action
        action_keywords = [
            'ls', 'cd', 'mkdir', 'cp', 'mv', 'rm', 'cat', 'grep', 'find', 'ps', 'top',
            'ping', 'curl', 'wget', 'git', 'docker', 'kubectl', 'ssh', 'scp'
        ]

        # Keywords that imply a question or generation, which should NOT auto-execute
        query_keywords = [
            'what', 'how', 'why', 'explain', 'describe', 'tell me', 'can you',
            'write', 'generate', 'create', 'make', 'code', 'script', 'website', 'what is'
        ]
        
        # Context-aware phrases that should NOT auto-execute (follow-up requests)
        context_phrases = [
            'run it', 'execute it', 'start it', 'launch it', 'host it', 'serve it',
            'on localhost', 'on port', 'in browser', 'open it', 'test it',
            'it is not', 'it is not running', 'not working', 'does not work',
            'add feature', 'add functionality', 'add function', 'improve', 'enhance', 'fix',
            'help me', 'can you', 'please', 'i need', 'i want', 'make it', 'modify',
            'change', 'update', 'extend', 'expand', 'include', 'implement'
        ]
        
        # If any query keyword is present, it's likely not a command to auto-execute.
        if any(keyword in input_lower for keyword in query_keywords):
            return False
            
        # If it's a context-aware phrase, don't auto-execute
        if any(phrase in input_lower for phrase in context_phrases):
            return False
            
        # Check for context-aware phrases that might start with capital letters
        context_starters = ['add', 'make', 'modify', 'change', 'update', 'extend', 'expand', 'include', 'implement', 'improve', 'enhance', 'fix']
        if any(input_lower.startswith(starter) for starter in context_starters):
            return False

        # If an action keyword is present, it's a strong signal to auto-execute.
        if any(keyword in input_lower for keyword in action_keywords):
            return True

        # Fallback: only auto-execute if it's a very specific system command
        if len(input_lower.split()) <= 3 and '?' not in input_lower:
             # Check if the first word is a known system command
            known_sys_commands = ['ls', 'cd', 'mkdir', 'cp', 'mv', 'rm', 'cat', 'grep', 'find', 'ps', 'top', 'pwd', 'whoami', 'date']
            if input_lower.split()[0] in known_sys_commands:
                return True

        return False

    def handle_auto_execution(self, user_input: str, shell_instance):
        """
        Parses and executes a command that has been identified for auto-execution.
        """
        console.print(f"🤖 [bold green]Auto-executing command:[/] '{user_input}'")
        
        # Check if we're in terminal mode
        if hasattr(shell_instance, 'terminal_mode') and shell_instance.terminal_mode:
            # In terminal mode, execute directly
            output, exit_code = shell_instance._execute_terminal_command(user_input)
            if exit_code == 0:
                console.print(f"[green]Output:[/green]\n{output}")
            else:
                console.print(f"[red]Error (exit code {exit_code}):[/red]\n{output}")
            return
        
        # This is a simplified router. A more advanced version could use the AI
        # to better understand the user's intent.
        input_lower = user_input.lower()

        # Delegate to the appropriate module or controller
        if "website" in input_lower and "host" in input_lower:
            shell_instance.website_generator.generate(user_input)
        elif "code" in input_lower and "run" in input_lower:
            shell_instance.code_generator.generate(user_input)
        elif "backup" in input_lower:
            # For simplicity, we define a common backup action here.
            # This could be made more dynamic.
            self.system_controller.execute_command("echo 'Simulating a backup action...'")
        else:
            # Default to treating it as a direct system command
            self.system_controller.execute_command(user_input)

    def start_monitoring(self):
        """Starts the background thread for scheduled tasks."""
        if self.is_monitoring:
            console.print("[yellow]Automation monitoring is already running.[/yellow]")
            return

        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitoring_thread.start()
        console.print("[green]Started background automation monitoring.[/green]")

    def stop_monitoring(self):
        """Stops the background monitoring thread."""
        if not self.is_monitoring:
            console.print("[yellow]Automation monitoring is not running.[/yellow]")
            return
            
        self.is_monitoring = False
        console.print("[red]Stopped background automation monitoring.[/red]")

    def _monitor_loop(self):
        """The core loop that runs in the background to check for scheduled tasks."""
        while self.is_monitoring:
            schedule.run_pending()
            time.sleep(1) # Check for tasks every second

    def schedule_task(self, task_function, interval_minutes: int):
        """
        Schedules a given function to run at a regular interval.
        Example: schedule.every(10).minutes.do(job)
        """
        try:
            schedule.every(interval_minutes).minutes.do(task_function)
            console.print(f"[green]Task scheduled to run every {interval_minutes} minutes.[/green]")
        except Exception as e:
            console.print(f"[bold red]Error scheduling task: {e}[/bold red]")


