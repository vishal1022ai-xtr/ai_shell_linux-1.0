# unified-ai-shell/modules/code_generator.py
import os
import subprocess
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

# A back-reference to the AIManager is needed to generate code.
# This will be passed during initialization. We use a forward reference for typing.
if "AIManager" not in globals():
    from typing import TypeVar
    AIManager = TypeVar("AIManager")

class CodeGenerator:
    """
    Handles the generation, saving, and execution of Python code based on user prompts.
    This module interacts with an AI model to create scripts for various tasks.
    """
    def __init__(self, ai_manager: AIManager, console: Console):
        self.ai_manager = ai_manager
        self.console = console
        self.generated_code_dir = Path.cwd() / "generated_code"
        # Ensure the directory for generated code exists
        self.generated_code_dir.mkdir(exist_ok=True)

    def _save_code(self, code: str, topic: str) -> Path:
        """Saves the provided code to a unique Python file."""
        # Sanitize the topic to create a valid filename
        safe_topic = "".join(c for c in topic.lower() if c.isalnum() or c in ('_', '-')).rstrip()
        filename = f"{safe_topic}_{int(Path.cwd().stat().st_ctime)}.py"
        filepath = self.generated_code_dir / filename
        
        try:
            filepath.write_text(code, encoding='utf-8')
            return filepath
        except Exception as e:
            self.console.print(f"[bold red]Error saving code to {filepath}: {e}[/bold red]")
            raise

    def _execute_code(self, filepath: Path) -> tuple[bool, str]:
        """Executes a Python script and captures its output."""
        try:
            # Use the same Python interpreter that is running the shell
            result = subprocess.run(
                [sys.executable, str(filepath)],
                capture_output=True,
                text=True,
                timeout=60,  # 60-second timeout to prevent long-running scripts
                check=False
            )

            if result.returncode == 0:
                output = result.stdout.strip() if result.stdout else "[No output]"
                return True, output
            else:
                error_output = result.stderr.strip() if result.stderr else "[No error message]"
                return False, error_output

        except subprocess.TimeoutExpired:
            return False, "Execution timed out after 60 seconds."
        except Exception as e:
            return False, f"An unexpected error occurred during execution: {e}"

    def generate_and_run(self, topic: str, prompt: str):
        """
        Main method to generate, save, and run code. It orchestrates the entire process.
        
        Args:
            topic: A short, sanitized topic for the code (e.g., "fibonacci_sequence").
            prompt: The full user prompt asking for code generation.
        """
        self.console.print(f"[cyan]Generating Python code for: '{topic}'...[/cyan]")

        # 1. Craft a detailed prompt for the AI to ensure high-quality code
        generation_prompt = f"""
        Generate a complete, self-contained, and runnable Python script for the following request: '{prompt}'.

        Requirements for the script:
        1.  **Complete and Runnable:** It must be a single script that can be executed directly without needing other files.
        2.  **Well-Documented:** Include comments and a docstring explaining what the code does and how to run it.
        3.  **User-Friendly Output:** The script should print clear, user-friendly output to the console so the user knows what it's doing.
        4.  **Error Handling:** Include basic error handling where appropriate (e.g., for user input).
        5.  **Standard Libraries:** Prefer standard Python libraries. If a third-party library is essential, mention it in a comment (e.g., # requires: requests).

        Please provide ONLY the Python code inside a single code block.
        """

        try:
            # 2. Get the code from the AI model (GPT-OSS is good for this)
            generated_code, model_used = self.ai_manager.get_response(generation_prompt, task_type="execution")
            
            # Clean up the response to get only the code
            if "```python" in generated_code:
                generated_code = generated_code.split("```python\n")[1].split("```")[0]
            elif "```" in generated_code:
                 generated_code = generated_code.split("```\n")[1].split("```")[0]


            self.console.print(f"[green]Code generated successfully using {model_used}.[/green]")
            
            # 3. Save the code to a file
            code_filepath = self._save_code(generated_code, topic)
            self.console.print(f"Code saved to: [bold cyan]{code_filepath}[/bold cyan]")

            # Display the generated code with syntax highlighting
            self.console.print(Panel(Syntax(generated_code, "python", theme="monokai", line_numbers=True), title="Generated Code", border_style="blue"))

            # 4. Execute the code
            self.console.print(f"\n[cyan]Executing script: {code_filepath.name}...[/cyan]")
            success, output = self._execute_code(code_filepath)

            # 5. Report the result
            if success:
                result_panel = Panel(
                    f"[bold green]✅ Script executed successfully![/bold green]\n\n[bold]Output:[/bold]\n{output}",
                    title="Execution Result",
                    border_style="green"
                )
            else:
                result_panel = Panel(
                    f"[bold red]❌ Script failed to execute.[/bold red]\n\n[bold]Error:[/bold]\n{output}",
                    title="Execution Result",
                    border_style="red"
                )
            self.console.print(result_panel)

        except Exception as e:
            self.console.print(f"[bold red]Code generation process failed: {e}[/bold red]")


