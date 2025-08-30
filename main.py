# unified-ai-shell/main.py
import sys
from pathlib import Path
from rich.console import Console

# To ensure that the core and modules packages can be found, we add the project root to the Python path.
# This allows for clean imports like `from core.shell import AIShell`.
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))

from config.config_manager import ConfigManager
from core.shell import AIShell

console = Console()

def run_shell():
    """
    Initializes and runs the Unified AI Shell.
    This is the main function that kicks everything off.
    """
    try:
        # 1. Initialize the configuration manager, which will load 'config/ultra_config.ini'
        console.print("[cyan]Loading configuration...[/cyan]")
        config_manager = ConfigManager()

        # 2. Create the main AIShell instance, passing the configuration to it.
        # The AIShell's __init__ method will then initialize all other subsystems.
        console.print("[cyan]Initializing AI subsystems...[/cyan]")
        shell = AIShell(config_manager)

        # 3. Start the main interactive loop of the shell.
        # This function will run until the user types '/exit'.
        shell.run()

    except FileNotFoundError as e:
        console.print(f"[bold red]Error: A required file was not found.[/bold red]")
        console.print(f"[red]Details: {e}[/red]")
        console.print("[yellow]Please ensure the directory structure is correct and all files are in place.[/yellow]")
        sys.exit(1)
    except ImportError as e:
        console.print(f"[bold red]Error: A required library is not installed.[/bold red]")
        console.print(f"[red]Details: {e}[/red]")
        console.print("[yellow]Please run 'pip install -r requirements.txt' to install dependencies.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]A fatal error occurred during startup: {e}[/bold red]")
        # For debugging, you can uncomment the next line to see the full traceback
        # console.print_exception(show_locals=True)
        sys.exit(1)

if __name__ == "__main__":
    # This block ensures the code only runs when the script is executed directly
    # (e.g., `python main.py`) and not when imported as a module.
    run_shell()


