# core/ai_manager.py
import google.generativeai as genai
from groq import Groq
from rich.console import Console

# Import the ConfigManager from the config directory
from config.config_manager import ConfigManager

console = Console()

class AIManager:
    """Handles interactions with Groq and Gemini AI models, including smart routing."""
    def __init__(self, config: ConfigManager):
        self.config = config
        self.groq_client = None
        self.gemini_model = None
        self._initialize_clients()

    def _initialize_clients(self):
        """Initializes the API clients for Groq and Gemini."""
        try:
            groq_api_key = self.config.get('API_KEYS', 'groq_api_key')
            gemini_api_key = self.config.get('API_KEYS', 'gemini_api_key')

            if 'your_groq_key_here' in groq_api_key or not groq_api_key:
                console.print("[bold yellow]Warning: Groq API key is not set in config/ultra_config.ini. Groq model will be unavailable.[/bold yellow]")
            else:
                self.groq_client = Groq(api_key=groq_api_key)

            if 'your_gemini_key_here' in gemini_api_key or not gemini_api_key:
                console.print("[bold yellow]Warning: Gemini API key is not set in config/ultra_config.ini. Gemini model will be unavailable.[/bold yellow]")
            else:
                genai.configure(api_key=gemini_api_key)
                self.gemini_model = genai.GenerativeModel(self.config.get('MODELS', 'gemini_model'))

        except Exception as e:
            console.print(f"[bold red]Fatal Error initializing AI models: {e}[/bold red]")
            console.print("[bold red]Please check your API keys and configuration in 'config/ultra_config.ini'.[/bold red]")


    def _determine_task_type(self, prompt: str) -> str:
        """Determines if a task is better suited for fast execution or complex analysis."""
        # Simple keywords indicating a need for speed and direct action
        execution_keywords = [
            'run', 'execute', 'list', 'show', 'make', 'ls', 'cd', 'status', 'start', 'host'
        ]
        # Keywords indicating a need for reasoning, creativity, or deep understanding
        analysis_keywords = [
            'explain', 'what is', 'how does', 'why', 'analyze', 'summarize', 'write', 'create', 'generate'
        ]
        # Keywords indicating user needs help or has issues
        help_keywords = [
            'help', 'not working', 'does not work', 'error', 'problem', 'issue', 'fix', 'broken',
            'not running', 'failed', 'troubleshoot', 'debug', 'what went wrong'
        ]
        # Specialized task types
        web_content_keywords = [
            'website', 'web', 'html', 'css', 'page', 'site', 'frontend', 'ui', 'design'
        ]
        code_generation_keywords = [
            'code', 'script', 'program', 'function', 'class', 'algorithm', 'logic', 'software'
        ]

        prompt_lower = prompt.lower()
        
        # Check for specialized task types first
        if any(keyword in prompt_lower for keyword in web_content_keywords):
            return 'web_content'
        if any(keyword in prompt_lower for keyword in code_generation_keywords):
            return 'code_generation'
        
        # Check for help/issue keywords
        if any(keyword in prompt_lower for keyword in help_keywords):
            return 'analysis'  # Help requests need detailed analysis
            
        # Prioritize execution keywords if present
        if any(keyword in prompt_lower for keyword in execution_keywords):
            return 'execution'
        if any(keyword in prompt_lower for keyword in analysis_keywords):
            return 'analysis'
            
        # Default to analysis for general queries
        return 'analysis'

    def get_ai_response(self, prompt: str, model_preference: str = 'auto') -> tuple[str, str]:
        """
        Gets a response from the best-suited AI model based on smart routing.

        Returns:
            A tuple containing (response_text, model_name_used).
        """
        task_type = self._determine_task_type(prompt)
        
        # --- Smart Routing Logic ---
        if model_preference == 'auto':
            if task_type == 'execution':
                chosen_model_type = self.config.get('MODELS', 'execution_model', 'groq')
            elif task_type in ['web_content', 'code_generation']:
                # Specialized creative tasks use Gemini (planning model)
                chosen_model_type = self.config.get('MODELS', 'planning_model', 'gemini')
            else: # analysis and other tasks
                chosen_model_type = self.config.get('MODELS', 'planning_model', 'gemini')
        else:
            chosen_model_type = model_preference

        console.print(f"🤖 Routing to [bold yellow]{chosen_model_type.upper()}[/bold yellow] for a '{task_type}' task...")

        try:
            if chosen_model_type == 'groq' and self.groq_client:
                model_name = self.config.get('MODELS', 'groq_model')
                chat_completion = self.groq_client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=1,
                    max_completion_tokens=8192,
                    top_p=1,
                    reasoning_effort="medium",
                    stream=False,
                    stop=None
                )
                response_text = chat_completion.choices[0].message.content
                return response_text, f"Groq ({model_name})"
                
            elif chosen_model_type == 'gemini' and self.gemini_model:
                model_name = self.config.get('MODELS', 'gemini_model')
                response = self.gemini_model.generate_content(prompt)
                return response.text, f"Gemini ({model_name})"
            else:
                return f"Model '{chosen_model_type}' is not available. Please check configuration.", "Error"

        except Exception as e:
            console.print(f"[bold red]Error communicating with {chosen_model_type.upper()}: {e}[/bold red]")
            
            # Check if it's a Gemini quota error and try to fallback to Groq
            if chosen_model_type == 'gemini' and '429' in str(e) and self.groq_client:
                console.print("[yellow]Gemini quota exceeded, falling back to Groq...[/yellow]")
                try:
                    model_name = self.config.get('MODELS', 'groq_model')
                    chat_completion = self.groq_client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=1,
                        max_completion_tokens=8192,
                        top_p=1,
                        reasoning_effort="medium",
                        stream=False,
                        stop=None
                    )
                    response_text = chat_completion.choices[0].message.content
                    return response_text, f"Groq ({model_name}) [Fallback]"
                except Exception as groq_error:
                    console.print(f"[bold red]Groq fallback also failed: {groq_error}[/bold red]")
                    return f"Both Gemini and Groq failed. Gemini error: {e}. Groq error: {groq_error}", "Error"
            
            # Check if it's a Groq error and try to fallback to Gemini
            elif chosen_model_type == 'groq' and self.gemini_model:
                console.print("[yellow]Groq failed, falling back to Gemini...[/yellow]")
                try:
                    model_name = self.config.get('MODELS', 'gemini_model')
                    response = self.gemini_model.generate_content(prompt)
                    return response.text, f"Gemini ({model_name}) [Fallback]"
                except Exception as gemini_error:
                    console.print(f"[bold red]Gemini fallback also failed: {gemini_error}[/bold red]")
                    return f"Both Groq and Gemini failed. Groq error: {e}. Gemini error: {gemini_error}", "Error"
            
            return f"An error occurred with the {chosen_model_type.upper()} API.", "Error"

    def classify_task(self, user_input: str) -> str:
        """
        Classify the type of task based on user input.
        This is an alias for _determine_task_type for consistency with the shell interface.
        
        Args:
            user_input: The user's input string
            
        Returns:
            Task type: 'execution' or 'analysis'
        """
        return self._determine_task_type(user_input)
    
    def get_response(self, user_input: str, task_type: str = None) -> tuple[str, str]:
        """
        Get a response from the AI for the given user input.
        This is the main interface method used by the shell.
        
        Args:
            user_input: The user's input string
            task_type: The type of task (optional, will be determined if not provided)
            
        Returns:
            A tuple containing (response_text, model_name_used)
        """
        if task_type is None:
            task_type = self.classify_task(user_input)
        
        return self.get_ai_response(user_input, model_preference='auto')
    
    def get_response_with_context(self, user_input: str, conversation_history: list, task_type: str = None) -> tuple[str, str]:
        """
        Get a response from the AI with full conversation context.
        This method maintains conversation awareness.
        
        Args:
            user_input: The user's input string
            conversation_history: List of previous conversation turns
            task_type: The type of task (optional, will be determined if not provided)
            
        Returns:
            A tuple containing (response_text, model_name_used)
        """
        if task_type is None:
            task_type = self.classify_task(user_input)
        
        # Build context-aware prompt
        context_prompt = self._build_context_prompt(user_input, conversation_history)
        
        return self.get_ai_response(context_prompt, model_preference='auto')
    
    def _build_context_prompt(self, current_input: str, conversation_history: list) -> str:
        """
        Build a context-aware prompt that includes conversation history.
        
        Args:
            current_input: The current user input
            conversation_history: List of previous conversation turns
            
        Returns:
            A context-aware prompt string
        """
        if not conversation_history:
            return current_input
        
        # Build conversation context
        context_lines = []
        for turn in conversation_history[-10:]:  # Keep last 10 turns for context
            role = turn["role"]
            content = turn["content"]
            if role == "user":
                context_lines.append(f"User: {content}")
            elif role == "assistant":
                context_lines.append(f"Assistant: {content}")
        
        # Add current input
        context_lines.append(f"User: {current_input}")
        
        # Join with clear separators
        context_prompt = "\n".join(context_lines)
        
        return context_prompt
    
    def read_file(self, filepath: str) -> str:
        """
        Read a file and return its contents.
        
        Args:
            filepath: Path to the file to read
            
        Returns:
            File contents as string
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: File '{filepath}' not found."
        except PermissionError:
            return f"Error: Permission denied reading '{filepath}'."
        except Exception as e:
            return f"Error reading file: {e}"
    
    def write_file(self, filepath: str, content: str) -> str:
        """
        Write content to a file.
        
        Args:
            filepath: Path to the file to write
            content: Content to write to the file
            
        Returns:
            Success message or error message
        """
        try:
            # Create directory if it doesn't exist (only if there's a directory path)
            import os
            dirname = os.path.dirname(filepath)
            if dirname:  # Only create directory if there's a path
                os.makedirs(dirname, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote {len(content)} characters to '{filepath}'"
        except PermissionError:
            return f"Error: Permission denied writing to '{filepath}'."
        except Exception as e:
            return f"Error writing file: {e}"
    
    def append_file(self, filepath: str, content: str) -> str:
        """
        Append content to a file.
        
        Args:
            filepath: Path to the file to append to
            content: Content to append
            
        Returns:
            Success message or error message
        """
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully appended {len(content)} characters to '{filepath}'"
        except FileNotFoundError:
            return f"Error: File '{filepath}' not found."
        except PermissionError:
            return f"Error: Permission denied appending to '{filepath}'."
        except Exception as e:
            return f"Error appending to file: {e}"
    
    def list_directory(self, path: str = ".") -> str:
        """
        List contents of a directory.
        
        Args:
            path: Directory path to list
            
        Returns:
            Directory listing as string
        """
        try:
            import os
            items = os.listdir(path)
            result = f"Contents of '{path}':\n"
            for item in sorted(items):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    result += f"📁 {item}/\n"
                else:
                    result += f"📄 {item}\n"
            return result
        except FileNotFoundError:
            return f"Error: Directory '{path}' not found."
        except PermissionError:
            return f"Error: Permission denied accessing '{path}'."
        except Exception as e:
            return f"Error listing directory: {e}"
    
    def file_exists(self, filepath: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            filepath: Path to the file
            
        Returns:
            True if file exists, False otherwise
        """
        import os
        return os.path.exists(filepath)
    
    def get_file_info(self, filepath: str) -> str:
        """
        Get information about a file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            File information as string
        """
        try:
            import os
            import stat
            from datetime import datetime
            
            if not os.path.exists(filepath):
                return f"Error: File '{filepath}' not found."
            
            stat_info = os.stat(filepath)
            size = stat_info.st_size
            modified = datetime.fromtimestamp(stat_info.st_mtime)
            permissions = stat.filemode(stat_info.st_mode)
            
            info = f"File: {filepath}\n"
            info += f"Size: {size} bytes\n"
            info += f"Modified: {modified}\n"
            info += f"Permissions: {permissions}\n"
            
            if os.path.isdir(filepath):
                info += "Type: Directory\n"
            else:
                info += "Type: File\n"
            
            return info
        except Exception as e:
            return f"Error getting file info: {e}"
    
    def display_response(self, response: str, model_used: str, response_time: float):
        """
        Display the AI response with formatting and metadata.
        
        Args:
            response: The AI response text
            model_used: The name of the model used
            response_time: Time taken to generate the response
        """
        console.print(f"\n[bold cyan]AI Response ({model_used}):[/bold cyan]")
        console.print(f"[green]{response}[/green]")
        console.print(f"\n[dim]Response time: {response_time:.2f}s[/dim]\n")

    def interpret_command(self, user_input: str, available_commands: list) -> str:
        """
        Uses an AI model to interpret a natural language query and map it to a specific shell command.
        
        Returns:
            The interpreted command string or an empty string if no mapping is found.
        """
        # System prompt engineering for precise output
        system_prompt = f"""
        You are an intelligent router for a command-line shell. Your only job is to map the user's natural language input to one of the available internal commands.

        Respond ONLY with the single, executable command line. Do not add any explanation, context, or surrounding text.

        Available commands: {', '.join(available_commands)}

        ---
        Example 1:
        User Input: "Show me the files in the current directory"
        Your Response: ls

        Example 2:
        User Input: "I want to build a website for my dog walking business"
        Your Response: website a professional website for a dog walking business

        Example 3:
        User Input: "what's the cpu usage like?"
        Your Response: status
        
        Example 4:
        User Input: "write a python script to calculate pi and then run it"
        Your Response: code a python script to calculate pi

        Example 5:
        User Input: "help me"
        Your Response: help
        ---

        Now, interpret the following user input.

        User Input: "{user_input}"
        Your Response:
        """

        # Gemini is preferred for this reasoning task
        command_to_run, model_used = self.get_ai_response(system_prompt, model_preference='gemini')
        
        # Clean up the response to ensure it's a valid command
        if command_to_run:
            # Remove potential markdown code blocks
            command_to_run = command_to_run.replace("```", "").strip()
            # Split to get the first word, which should be the command
            base_command = command_to_run.split()[0]
            if base_command in available_commands:
                return command_to_run
            else:
                console.print(f"[yellow]Warning: AI suggested an unknown command '{base_command}'. Falling back to general query.[/yellow]")
                return "" # Return empty if the interpreted command is not valid
        return ""
    
    def check_api_health(self) -> dict:
        """
        Check the health status of both AI APIs.
        
        Returns:
            Dictionary with health status of each API
        """
        health_status = {
            'groq': {'status': 'unknown', 'error': None},
            'gemini': {'status': 'unknown', 'error': None}
        }
        
        # Test Groq API
        if self.groq_client:
            try:
                test_response = self.groq_client.chat.completions.create(
                    model=self.config.get('MODELS', 'groq_model'),
                    messages=[{"role": "user", "content": "test"}],
                    max_completion_tokens=10,
                    stream=False
                )
                health_status['groq']['status'] = 'healthy'
            except Exception as e:
                health_status['groq']['status'] = 'error'
                health_status['groq']['error'] = str(e)
        
        # Test Gemini API
        if self.gemini_model:
            try:
                test_response = self.gemini_model.generate_content("test")
                health_status['gemini']['status'] = 'healthy'
            except Exception as e:
                health_status['gemini']['status'] = 'error'
                health_status['gemini']['error'] = str(e)
        
        return health_status
    
    def get_best_available_model(self, task_type: str) -> str:
        """
        Get the best available model for a given task type.
        Automatically falls back to available models if preferred one fails.
        
        Args:
            task_type: The type of task ('execution' or 'analysis')
            
        Returns:
            The best available model type
        """
        health_status = self.check_api_health()
        
        # Determine preferred model based on task type
        if task_type == 'execution':
            preferred = 'groq'
            fallback = 'gemini'
        else:  # analysis
            preferred = 'gemini'
            fallback = 'groq'
        
        # Check if preferred model is healthy
        if health_status[preferred]['status'] == 'healthy':
            return preferred
        
        # Check if fallback model is healthy
        if health_status[fallback]['status'] == 'healthy':
            console.print(f"[yellow]Preferred model '{preferred}' unavailable, using '{fallback}'[/yellow]")
            return fallback
        
        # Both models are unhealthy
        console.print("[bold red]Both AI models are currently unavailable![/bold red]")
        return 'none'


