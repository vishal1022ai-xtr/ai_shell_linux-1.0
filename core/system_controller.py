# core/system_controller.py
import os
import subprocess
import shutil
from pathlib import Path
import psutil
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm

# Initialize a Rich console for beautiful, consistent output
console = Console()

class SystemController:
    """
    Handles all direct interactions with the operating system, including
    file operations, command execution, and system monitoring.
    Includes safety features for destructive operations.
    """
    def __init__(self):
        self.safety_mode = True
        # A set of keywords that trigger a confirmation prompt if safety_mode is on
        self.DESTRUCTIVE_COMMANDS = {
            "rm", "del", "delete", "remove", "format", "wipe", "shutdown", "reboot"
        }

    def _confirm_action(self, action: str, target: str) -> bool:
        """Asks the user for confirmation before performing a dangerous action."""
        if not self.safety_mode:
            return True  # Safety mode is off, so always approve the action
        
        return Confirm.ask(
            f"[bold yellow]⚠️ Are you sure you want to {action} '[cyan]{target}[/cyan]'?[/bold yellow]",
            default=False,
            console=console
        )

    def execute_command(self, command: str):
        """
        Executes a shell command, with safety checks for potentially
        destructive operations.
        """
        # Check if the command contains any destructive keywords
        command_parts = command.split()
        if any(part in self.DESTRUCTIVE_COMMANDS for part in command_parts):
            if not self._confirm_action("execute command", command):
                console.print("[yellow]Operation cancelled by user.[/yellow]")
                return

        try:
            console.print(f"[cyan]Executing: {command}[/cyan]")
            # Use subprocess.run to execute the command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=False  # Don't raise an exception for non-zero exit codes
            )
            # Print stdout if there is any
            if result.stdout:
                console.print("[green]Output:[/green]")
                console.print(result.stdout.strip())
            # Print stderr if there is any, indicating an error
            if result.stderr:
                console.print("[bold red]Error:[/bold red]")
                console.print(result.stderr.strip())

        except FileNotFoundError:
            console.print(f"[bold red]Error: Command not found: '{command_parts[0]}'[/bold red]")
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")

    def get_status(self):
        """Displays a rich table with current system status (CPU, Memory, Disk)."""
        table = Table(title="🖥️ System Status", border_style="blue")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Usage", style="magenta")
        table.add_column("Details", justify="right", style="green")

        # CPU Info
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_color = "red" if cpu_percent > 80 else "green"
        table.add_row("CPU", f"[{cpu_color}]{cpu_percent}%[/{cpu_color}]", f"{psutil.cpu_count(logical=False)} Cores, {psutil.cpu_count(logical=True)} Threads")

        # Memory Info
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        mem_color = "red" if mem_percent > 80 else "green"
        table.add_row("Memory", f"[{mem_color}]{mem_percent}%[/{mem_color}]", f"{mem.used / (1024**3):.2f} / {mem.total / (1024**3):.2f} GB")

        # Disk Info (for the root directory)
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_color = "red" if disk_percent > 80 else "green"
        table.add_row("Disk", f"[{disk_color}]{disk_percent}%[/{disk_color}]", f"{disk.used / (1024**3):.2f} / {disk.total / (1024**3):.2f} GB")
        
        console.print(table)

    def list_directory(self, path_str: str = "."):
        """Lists the contents of a directory in a formatted table."""
        target_path = Path(path_str).resolve()
        if not target_path.exists():
            console.print(f"[bold red]Error: Path '{target_path}' does not exist.[/bold red]")
            return
        if not target_path.is_dir():
            console.print(f"[bold red]Error: '{target_path}' is not a directory.[/bold red]")
            return

        table = Table(title=f"📁 Contents of {target_path}", border_style="yellow")
        table.add_column("Type", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Size (Bytes)", justify="right", style="magenta")
        table.add_column("Last Modified", style="green")

        try:
            for item in sorted(target_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
                stat = item.stat()
                item_type = "📄" if item.is_file() else " D" if item.is_dir() else "🔗"
                size = stat.st_size if item.is_file() else ""
                modified_time = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                table.add_row(item_type, item.name, str(size), modified_time)
        except PermissionError:
            console.print(f"[bold red]Error: Permission denied to access '{target_path}'.[/bold red]")
            return
            
        console.print(table)

    def create_directory(self, path_str: str):
        """Creates a new directory."""
        target_path = Path(path_str)
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]Successfully created directory: '{target_path.resolve()}'[/green]")
        except Exception as e:
            console.print(f"[bold red]Error creating directory: {e}[/bold red]")
            
    def delete_path(self, path_str: str):
        """Deletes a file or directory, with confirmation."""
        target_path = Path(path_str).resolve()
        if not target_path.exists():
            console.print(f"[bold red]Error: Path '{target_path}' does not exist.[/bold red]")
            return

        action_type = "recursively delete directory" if target_path.is_dir() else "delete file"
        if self._confirm_action(action_type, str(target_path)):
            try:
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()
                console.print(f"[green]Successfully deleted: '{target_path}'[/green]")
            except Exception as e:
                console.print(f"[bold red]Error deleting path: {e}[/bold red]")
        else:
            console.print("[yellow]Deletion cancelled.[/yellow]")

    def copy_path(self, source_str: str, dest_str: str):
        """Copies a file or directory."""
        source_path = Path(source_str).resolve()
        dest_path = Path(dest_str)
        if not source_path.exists():
            console.print(f"[bold red]Error: Source path '{source_path}' does not exist.[/bold red]")
            return

        try:
            if source_path.is_dir():
                shutil.copytree(source_path, dest_path)
            else:
                shutil.copy2(source_path, dest_path)
            console.print(f"[green]Successfully copied '{source_path}' to '{dest_path.resolve()}'[/green]")
        except Exception as e:
            console.print(f"[bold red]Error copying: {e}[/bold red]")

    def move_path(self, source_str: str, dest_str: str):
        """Moves a file or directory."""
        source_path = Path(source_str).resolve()
        dest_path = Path(dest_str)
        if not source_path.exists():
            console.print(f"[bold red]Error: Source path '{source_path}' does not exist.[/bold red]")
            return
        
        try:
            shutil.move(str(source_path), str(dest_path))
            console.print(f"[green]Successfully moved '{source_path}' to '{dest_path.resolve()}'[/green]")
        except Exception as e:
            console.print(f"[bold red]Error moving: {e}[/bold red]")


