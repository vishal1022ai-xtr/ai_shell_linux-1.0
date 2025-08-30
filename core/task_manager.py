# core/task_manager.py
import datetime
import uuid
from typing import Dict, Any, Callable, List
from rich.console import Console
from rich.table import Table

console = Console()

class Task:
    """Represents a single manageable task within the shell."""
    def __init__(self, name: str, action: Callable, description: str, persistent: bool = False):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.action = action
        self.description = description
        self.persistent = persistent
        self.status = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED
        self.created_at = datetime.datetime.now()
        self.last_run = None
        self.run_count = 0
        self.last_result = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the task's state to a dictionary for display."""
        return {
            "ID": self.id,
            "Name": self.name,
            "Description": self.description,
            "Status": self.status,
            "Created At": self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "Last Run": self.last_run.strftime('%Y-%m-%d %H:%M:%S') if self.last_run else "N/A",
            "Run Count": str(self.run_count),
        }

class TaskManager:
    """
    Manages the lifecycle of tasks, including creation, tracking,
    and providing status updates. Does not execute tasks directly but holds
    their definitions for the AutomationEngine.
    """
    def __init__(self):
        self.tasks: Dict[str, Task] = {}

    def add_task(self, name: str, action: Callable, description: str, persistent: bool = False) -> Task:
        """
        Defines and registers a new task.
        
        Args:
            name: A user-friendly name for the task.
            action: The function to be executed for this task.
            description: A brief description of what the task does.
            persistent: If True, the task will be saved and reloaded across sessions.

        Returns:
            The created Task object.
        """
        if name in [task.name for task in self.tasks.values()]:
            console.print(f"[yellow]Warning: Task with name '{name}' already exists. Overwriting.[/yellow]")
        
        new_task = Task(name=name, action=action, description=description, persistent=persistent)
        self.tasks[new_task.id] = new_task
        console.print(f"[green]Task '{name}' (ID: {new_task.id}) has been registered.[/green]")
        return new_task

    def get_task(self, task_id: str) -> Task | None:
        """Retrieves a task by its ID."""
        return self.tasks.get(task_id)

    def update_task_status(self, task_id: str, status: str, result: Any = None):
        """Updates the status and metadata of a task after an execution attempt."""
        task = self.get_task(task_id)
        if task:
            task.status = status.upper()
            task.last_run = datetime.datetime.now()
            if status.upper() != "FAILED":
                task.run_count += 1
            task.last_result = str(result)
        else:
            console.print(f"[bold red]Error: Cannot update status for non-existent task ID '{task_id}'.[/bold red]")

    def list_tasks(self):
        """Displays a formatted table of all registered tasks."""
        if not self.tasks:
            console.print("[yellow]No tasks have been registered yet.[/yellow]")
            return

        table = Table(title="📋 Registered Tasks", border_style="magenta")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
        table.add_column("Status", style="yellow")
        table.add_column("Last Run", style="green")
        table.add_column("Run Count", justify="right", style="blue")
        table.add_column("Description", style="default")

        for task in self.tasks.values():
            task_info = task.to_dict()
            status_color = "green" if task.status == "COMPLETED" else "yellow" if task.status == "PENDING" else "red"
            table.add_row(
                task_info["ID"],
                task_info["Name"],
                f"[{status_color}]{task_info['Status']}[/{status_color}]",
                task_info["Last Run"],
                task_info["Run Count"],
                task_info["Description"]
            )
        
        console.print(table)


