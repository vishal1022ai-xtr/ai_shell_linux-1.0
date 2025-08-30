# core/__init__.py

"""
This file makes the 'core' directory a Python package.

It also simplifies imports by exposing the main classes from each module
at the top level of the package. This allows for cleaner imports in main.py,
for example: from core import AIShell, AIManager
"""

from .shell import AIShell
from .ai_manager import AIManager
from .system_controller import SystemController
from .task_manager import TaskManager
from .learning_system import LearningSystem
from .automation import AutomationEngine

# Defines the public API of the 'core' package
__all__ = [
    "AIShell",
    "AIManager",
    "SystemController",
    "TaskManager",
    "LearningSystem",
    "AutomationEngine",
]


