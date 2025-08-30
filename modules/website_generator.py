# unified-ai-shell/modules/website_generator.py
import os
import http.server
import socketserver
import threading
import webbrowser
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# A back-reference to the AIManager is needed to generate content.
# This will be passed during initialization. We use a forward reference for typing.
if "AIManager" not in globals():
    from typing import TypeVar
    AIManager = TypeVar("AIManager")

class WebsiteGenerator:
    """
    Handles the generation and local hosting of a website based on a user's prompt.
    It uses an AI model to create modern, responsive HTML and CSS content.
    """
    def __init__(self, ai_manager: AIManager, console: Console):
        self.ai_manager = ai_manager
        self.console = console
        self.generated_sites_dir = Path.cwd() / "generated_websites"
        # Ensure the directory for generated sites exists
        self.generated_sites_dir.mkdir(exist_ok=True)

    def _start_hosting_server(self, directory: Path, port: int):
        """Starts a simple Python HTTP server in a background thread."""
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(directory), **kwargs)

        # Allow the OS to reuse the address to prevent errors on quick restarts
        socketserver.TCPServer.allow_reuse_address = True
        httpd = socketserver.TCPServer(("", port), Handler)

        def serve_forever():
            self.console.print(f"[bold green]✓ Server started![/bold green] Find your website at: [link=http://localhost:{port}]http://localhost:{port}[/link]")
            self.console.print("[yellow](Press Ctrl+C in the main shell to stop the server and the shell)[/yellow]")
            httpd.serve_forever()

        # Run the server in a daemon thread so it automatically shuts down
        # when the main application exits.
        server_thread = threading.Thread(target=serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        # Open the website in a new browser tab for convenience
        try:
            webbrowser.open(f"http://localhost:{port}")
        except Exception:
            self.console.print("[yellow]Could not automatically open browser. Please navigate to the URL above.[/yellow]")


    def generate_and_host(self, topic: str, prompt: str):
        """
        Main method to generate, save, and host a website.
        
        Args:
            topic: A short, user-provided topic for the website (e.g., "footwear").
            prompt: The full user prompt asking for the website.
        """
        self.console.print(f"[cyan]Generating a website about: '{topic}'...[/cyan]")

        # 1. Craft a detailed prompt for the AI to get a high-quality, single-file website.
        generation_prompt = f"""
        Generate the complete HTML and CSS code for a visually appealing, modern, and professional-looking single-page website based on the following request: '{prompt}'.

        **Key Requirements for the Website:**
        1.  **Single File:** All HTML and CSS must be in a single `index.html` file. Use an internal `<style>` tag for all CSS. Do not link to external CSS files.
        2.  **Responsive Design:** The layout must be fully responsive and look great on mobile phones, tablets, and desktops. Use media queries.
        3.  **Modern Aesthetics:**
            - Use a clean, professional font like 'Inter' or 'Poppins' from Google Fonts.
            - Employ a modern gradient background for the body.
            - Use a card-based layout to present information in distinct, visually pleasing blocks.
            - All elements (cards, buttons, images) should have rounded corners (`border-radius`).
        4.  **Content:** Generate relevant, high-quality placeholder text, headlines, and sections based on the topic of '{topic}'. Include sections like "About Us," "Our Products/Services," and "Contact."
        5.  **No JavaScript:** Do not include any JavaScript code unless it is absolutely essential for a basic feature.

        Please provide ONLY the complete HTML code for the `index.html` file, starting with `<!DOCTYPE html>`.
        """

        try:
            # 2. Get the website code from the AI (Gemini is good for creative content)
            website_html, model_used = self.ai_manager.get_response(generation_prompt, task_type="web_content")
            
            # Clean up the AI's response to ensure we only have the HTML code
            if "```html" in website_html:
                website_html = website_html.split("```html\n")[1].split("```")[0]
            
            self.console.print(f"[green]Website content generated successfully using {model_used}.[/green]")

            # 3. Create a unique directory and save the website
            safe_topic = "".join(c for c in topic.lower() if c.isalnum() or c in ('_', '-')).rstrip()
            site_dir = self.generated_sites_dir / f"{safe_topic}_{int(Path.cwd().stat().st_ctime)}"
            site_dir.mkdir(exist_ok=True)
            
            index_file = site_dir / "index.html"
            index_file.write_text(website_html, encoding='utf-8')
            
            self.console.print(f"Website saved to: [bold cyan]{site_dir}[/bold cyan]")

            # 4. Host the website on a local server
            port = 8000
            self.console.print(f"\n[cyan]Starting local server on port {port}...[/cyan]")
            self._start_hosting_server(site_dir, port)
            
            # Final summary panel
            summary_text = (
                f"Your new website on '{topic}' is live!\n\n"
                f"[bold]Directory:[/bold] {site_dir}\n"
                f"[bold]URL:[/bold] [link=http://localhost:{port}]http://localhost:{port}[/link]"
            )
            self.console.print(Panel(summary_text, title="🚀 Website Deployed Locally", border_style="green", expand=False))

        except Exception as e:
            self.console.print(f"[bold red]Website generation process failed: {e}[/bold red]")


