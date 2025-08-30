# core/ai_agent.py
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
import threading
import queue

console = Console()

class AIAgent:
    """An autonomous AI agent that can perform tasks independently."""
    
    def __init__(self, name: str, capabilities: List[str], ai_manager):
        self.name = name
        self.capabilities = capabilities
        self.ai_manager = ai_manager
        self.is_active = False
        self.task_queue = queue.Queue()
        self.results = []
        self.agent_thread = None
        self.performance_metrics = {
            'tasks_completed': 0,
            'success_rate': 0.0,
            'avg_response_time': 0.0
        }
    
    def start(self):
        """Start the agent's autonomous operation."""
        if self.is_active:
            console.print(f"[yellow]Agent {self.name} is already running.[/yellow]")
            return
        
        self.is_active = True
        self.agent_thread = threading.Thread(target=self._run_agent_loop, daemon=True)
        self.agent_thread.start()
        console.print(f"[green]🤖 Agent {self.name} is now active and autonomous![/green]")
    
    def stop(self):
        """Stop the agent."""
        self.is_active = False
        if self.agent_thread:
            self.agent_thread.join(timeout=1)
        console.print(f"[yellow]🤖 Agent {self.name} stopped.[/yellow]")
    
    def add_task(self, task: str, priority: int = 1):
        """Add a task to the agent's queue."""
        self.task_queue.put((priority, task, time.time()))
        console.print(f"[cyan]📋 Task added to {self.name}: {task}[/cyan]")
    
    def _run_agent_loop(self):
        """Main agent loop that processes tasks autonomously."""
        while self.is_active:
            try:
                if not self.task_queue.empty():
                    priority, task, timestamp = self.task_queue.get(timeout=1)
                    self._process_task(task, timestamp)
                else:
                    time.sleep(0.1)
            except queue.Empty:
                continue
            except Exception as e:
                console.print(f"[red]Agent {self.name} error: {e}[/red]")
    
    def _process_task(self, task: str, timestamp: float):
        """Process a single task using AI capabilities."""
        start_time = time.time()
        console.print(f"[cyan]🤖 {self.name} processing: {task}[/cyan]")
        
        try:
            # Use AI to understand and execute the task
            prompt = f"""
            You are an autonomous AI agent named {self.name} with capabilities: {', '.join(self.capabilities)}
            
            Task: {task}
            
            Analyze this task and provide a solution or execute it if possible.
            Be autonomous and take initiative to complete the task effectively.
            """
            
            response, model_used = self.ai_manager.get_ai_response(prompt, model_preference='auto')
            
            # Record the result
            result = {
                'task': task,
                'response': response,
                'model_used': model_used,
                'timestamp': timestamp,
                'processing_time': time.time() - start_time,
                'success': True
            }
            
            self.results.append(result)
            self.performance_metrics['tasks_completed'] += 1
            
            console.print(f"[green]✅ {self.name} completed task: {task[:50]}...[/green]")
            console.print(f"[dim]Response: {response[:100]}...[/dim]")
            
        except Exception as e:
            result = {
                'task': task,
                'response': str(e),
                'model_used': 'error',
                'timestamp': timestamp,
                'processing_time': time.time() - start_time,
                'success': False
            }
            self.results.append(result)
            console.print(f"[red]❌ {self.name} failed task: {task[:50]}...[/red]")
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent."""
        return {
            'name': self.name,
            'capabilities': self.capabilities,
            'is_active': self.is_active,
            'queue_size': self.task_queue.qsize(),
            'total_results': len(self.results),
            'performance': self.performance_metrics
        }

class AIAgentManager:
    """Manages multiple AI agents and their lifecycle."""
    
    def __init__(self, ai_manager):
        self.ai_manager = ai_manager
        self.agents: Dict[str, AIAgent] = {}
        self.agent_templates = {
            'code_reviewer': ['code analysis', 'bug detection', 'best practices'],
            'security_auditor': ['security analysis', 'vulnerability detection', 'compliance'],
            'performance_optimizer': ['performance analysis', 'optimization', 'profiling'],
            'documentation_writer': ['documentation', 'tutorials', 'user guides'],
            'data_analyzer': ['data analysis', 'visualization', 'insights'],
            'api_tester': ['API testing', 'load testing', 'validation']
        }
    
    def create_agent(self, name: str, agent_type: str = None, custom_capabilities: List[str] = None) -> AIAgent:
        """Create a new AI agent."""
        if name in self.agents:
            console.print(f"[yellow]Agent {name} already exists.[/yellow]")
            return self.agents[name]
        
        if agent_type and agent_type in self.agent_templates:
            capabilities = self.agent_templates[agent_type]
        elif custom_capabilities:
            capabilities = custom_capabilities
        else:
            capabilities = ['general tasks', 'problem solving', 'automation']
        
        agent = AIAgent(name, capabilities, self.ai_manager)
        self.agents[name] = agent
        
        console.print(f"[green]🤖 Created AI agent '{name}' with capabilities: {', '.join(capabilities)}[/green]")
        return agent
    
    def start_agent(self, name: str):
        """Start a specific agent."""
        if name in self.agents:
            self.agents[name].start()
        else:
            console.print(f"[red]Agent {name} not found.[/red]")
    
    def stop_agent(self, name: str):
        """Stop a specific agent."""
        if name in self.agents:
            self.agents[name].stop()
        else:
            console.print(f"[red]Agent {name} not found.[/red]")
    
    def list_agents(self):
        """List all agents and their status."""
        if not self.agents:
            console.print("[yellow]No agents created yet.[/yellow]")
            return
        
        table = Table(title="🤖 AI Agents Status", border_style="blue")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Capabilities", style="yellow")
        table.add_column("Tasks Completed", style="magenta")
        table.add_column("Queue Size", style="blue")
        
        for agent in self.agents.values():
            status = agent.get_status()
            status_text = "🟢 Active" if status['is_active'] else "🔴 Stopped"
            table.add_row(
                status['name'],
                status_text,
                ", ".join(status['capabilities'][:3]) + ("..." if len(status['capabilities']) > 3 else ""),
                str(status['performance']['tasks_completed']),
                str(status['queue_size'])
            )
        
        console.print(table)
    
    def get_agent(self, name: str) -> Optional[AIAgent]:
        """Get an agent by name."""
        return self.agents.get(name)
    
    def remove_agent(self, name: str):
        """Remove an agent."""
        if name in self.agents:
            if self.agents[name].is_active:
                self.agents[name].stop()
            del self.agents[name]
            console.print(f"[green]Removed agent {name}.[/green]")
        else:
            console.print(f"[red]Agent {name} not found.[/red]")
