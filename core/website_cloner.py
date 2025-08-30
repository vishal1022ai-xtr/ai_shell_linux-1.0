# core/website_cloner.py
import requests
import os
import re
import time
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from bs4 import BeautifulSoup
import urllib.parse
import json

console = Console()

class WebsiteCloner:
    """Website cloning system for ethical hacking and testing."""
    
    def __init__(self):
        self.cloned_sites_dir = Path("cloned_websites")
        self.cloned_sites_dir.mkdir(exist_ok=True)
        self.visited_urls = set()
        self.downloaded_files = set()
        
        self.config = {
            'max_depth': 3,
            'max_pages': 50,
            'download_assets': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def clone_website(self, target_url: str, output_dir: str = None):
        """Clone a complete website with all content."""
        console.print(f"[bold cyan]🌐 Starting Website Clone[/bold cyan]")
        console.print(f"[cyan]Target: {target_url}[/cyan]")
        
        if not output_dir:
            domain = urllib.parse.urlparse(target_url).netloc
            output_dir = self.cloned_sites_dir / domain
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create asset directories
        (output_dir / "assets" / "css").mkdir(parents=True, exist_ok=True)
        (output_dir / "assets" / "js").mkdir(parents=True, exist_ok=True)
        (output_dir / "assets" / "images").mkdir(parents=True, exist_ok=True)
        
        try:
            self._clone_recursive(target_url, output_dir, depth=0)
            self._create_local_server(output_dir)
            self._generate_report(output_dir)
            
            console.print(f"[green]✅ Website cloned successfully![/green]")
            console.print(f"[cyan]Output: {output_dir}[/cyan]")
            
        except Exception as e:
            console.print(f"[red]❌ Cloning failed: {e}[/red]")
    
    def _clone_recursive(self, url: str, output_dir: Path, depth: int):
        """Recursively clone website pages."""
        if depth > self.config['max_depth'] or len(self.visited_urls) >= self.config['max_pages']:
            return
        
        if url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        console.print(f"[cyan]📄 Cloning: {url}[/cyan]")
        
        try:
            # Download page
            response = requests.get(url, headers={'User-Agent': self.config['user_agent']}, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Process and save page
            processed_content = self._process_page(soup, url, output_dir)
            page_filename = self._get_page_filename(url)
            page_path = output_dir / page_filename
            page_path.write_text(processed_content, encoding='utf-8')
            
            # Download assets
            if self.config['download_assets']:
                self._download_assets(soup, url, output_dir)
            
            # Extract links for further cloning
            if depth < self.config['max_depth']:
                links = self._extract_links(soup, url)
                for link in links[:5]:  # Limit links per page
                    if self._should_clone_link(link, url):
                        time.sleep(0.5)  # Be respectful
                        self._clone_recursive(link, output_dir, depth + 1)
            
        except Exception as e:
            console.print(f"[red]❌ Error cloning {url}: {e}[/red]")
    
    def _process_page(self, soup: BeautifulSoup, original_url: str, output_dir: Path) -> str:
        """Process HTML content to update asset references."""
        base_url = urllib.parse.urlparse(original_url)
        
        # Update CSS links
        for css_link in soup.find_all('link', rel='stylesheet'):
            if css_link.get('href'):
                new_href = self._process_asset_url(css_link['href'], original_url, output_dir, 'css')
                css_link['href'] = new_href
        
        # Update JavaScript sources
        for script in soup.find_all('script', src=True):
            if script.get('src'):
                new_src = self._process_asset_url(script['src'], original_url, output_dir, 'js')
                script['src'] = new_src
        
        # Update image sources
        for img in soup.find_all('img'):
            if img.get('src'):
                new_src = self._process_asset_url(img['src'], original_url, output_dir, 'image')
                img['src'] = new_src
        
        # Update form actions
        for form in soup.find_all('form'):
            if form.get('action'):
                new_action = self._process_asset_url(form['action'], original_url, output_dir, 'html')
                form['action'] = new_action
        
        return str(soup)
    
    def _process_asset_url(self, asset_url: str, page_url: str, output_dir: Path, asset_type: str) -> str:
        """Process asset URL and return local path."""
        if not asset_url or asset_url.startswith('#'):
            return asset_url
        
        # Convert to absolute URL
        absolute_url = urllib.parse.urljoin(page_url, asset_url)
        
        # Download asset
        asset_filename = self._download_asset(absolute_url, output_dir, asset_type)
        
        if asset_filename:
            return f"assets/{asset_type}s/{asset_filename}"
        
        return asset_url
    
    def _download_asset(self, asset_url: str, output_dir: Path, asset_type: str) -> str:
        """Download an asset file."""
        if asset_url in self.downloaded_files:
            return ""
        
        try:
            response = requests.get(asset_url, headers={'User-Agent': self.config['user_agent']}, timeout=30)
            response.raise_for_status()
            
            # Generate filename
            filename = self._generate_filename(asset_url, asset_type)
            
            # Save file
            if asset_type == 'css':
                file_path = output_dir / "assets" / "css" / filename
            elif asset_type == 'js':
                file_path = output_dir / "assets" / "js" / filename
            elif asset_type == 'image':
                file_path = output_dir / "assets" / "images" / filename
            else:
                file_path = output_dir / "assets" / filename
            
            file_path.write_bytes(response.content)
            self.downloaded_files.add(asset_url)
            
            console.print(f"[green]  ✅ Downloaded: {filename}[/green]")
            return filename
            
        except Exception as e:
            console.print(f"[red]  ❌ Failed to download {asset_url}: {e}[/red]")
            return ""
    
    def _generate_filename(self, asset_url: str, asset_type: str) -> str:
        """Generate filename for asset."""
        original_filename = os.path.basename(urllib.parse.urlparse(asset_url).path)
        
        if not original_filename or '.' not in original_filename:
            if asset_type == 'css':
                original_filename = 'style.css'
            elif asset_type == 'js':
                original_filename = 'script.js'
            elif asset_type == 'image':
                original_filename = 'image.png'
            else:
                original_filename = 'asset'
        
        # Ensure unique filename
        base, ext = os.path.splitext(original_filename)
        counter = 1
        filename = original_filename
        
        while Path(filename).exists():
            filename = f"{base}_{counter}{ext}"
            counter += 1
        
        return filename
    
    def _download_assets(self, soup: BeautifulSoup, page_url: str, output_dir: Path):
        """Download all assets from a page."""
        # CSS files
        for css_link in soup.find_all('link', rel='stylesheet'):
            if css_link.get('href'):
                self._process_asset_url(css_link['href'], page_url, output_dir, 'css')
        
        # JavaScript files
        for script in soup.find_all('script', src=True):
            if script.get('src'):
                self._process_asset_url(script['src'], page_url, output_dir, 'js')
        
        # Images
        for img in soup.find_all('img'):
            if img.get('src'):
                self._process_asset_url(img['src'], page_url, output_dir, 'image')
    
    def _extract_links(self, soup: BeautifulSoup, page_url: str) -> list:
        """Extract all links from a page."""
        links = []
        base_domain = urllib.parse.urlparse(page_url).netloc
        
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            
            # Skip anchors, javascript, mailto, etc.
            if href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue
            
            # Convert to absolute URL
            absolute_url = urllib.parse.urljoin(page_url, href)
            
            # Only include links from the same domain
            if urllib.parse.urlparse(absolute_url).netloc == base_domain:
                links.append(absolute_url)
        
        return list(set(links))
    
    def _should_clone_link(self, link: str, current_url: str) -> bool:
        """Determine if a link should be cloned."""
        if link in self.visited_urls:
            return False
        
        # Skip file downloads
        file_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar']
        if any(link.lower().endswith(ext) for ext in file_extensions):
            return False
        
        # Skip admin/private areas
        private_paths = ['/admin', '/private', '/wp-admin', '/phpmyadmin']
        if any(path in link.lower() for path in private_paths):
            return False
        
        return True
    
    def _get_page_filename(self, url: str) -> str:
        """Generate filename for a page."""
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path
        
        if not path or path == '/':
            return 'index.html'
        
        filename = path.lstrip('/')
        
        if not filename.endswith('.html'):
            if '.' in filename:
                base, ext = os.path.splitext(filename)
                filename = f"{base}.html"
            else:
                filename = f"{filename}.html"
        
        # Replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        return filename
    
    def _create_local_server(self, output_dir: Path):
        """Create local server configuration."""
        # Python server
        server_script = f"""#!/usr/bin/env python3
import http.server
import socketserver
import os

PORT = 8000
os.chdir('{output_dir}')

with socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
    print(f"Server running at http://localhost:{{PORT}}")
    print("Press Ctrl+C to stop")
    httpd.serve_forever()
"""
        
        server_file = output_dir / "start_server.py"
        server_file.write_text(server_script)
        server_file.chmod(0o755)
        
        console.print(f"[green]✅ Local server script created: {server_file}[/green]")
    
    def _generate_report(self, output_dir: Path):
        """Generate cloning report."""
        report = f"""# Website Cloning Report

## Summary
- **Total Pages Cloned**: {len(self.visited_urls)}
- **Total Assets Downloaded**: {len(self.downloaded_files)}
- **Output Directory**: {output_dir}

## Cloned Pages
"""
        
        for url in sorted(self.visited_urls):
            report += f"- {url}\n"
        
        report += f"""
## How to Run
1. Navigate to: {output_dir}
2. Run: python3 start_server.py
3. Visit: http://localhost:8000

## File Structure
- `index.html` - Main page
- `assets/` - CSS, JS, and images
- `start_server.py` - Local server script

## Legal Notice
This clone is for educational purposes only. Ensure you have permission to clone any website.
"""
        
        report_file = output_dir / "CLONING_REPORT.md"
        report_file.write_text(report)
        
        console.print(f"[green]✅ Cloning report generated: {report_file}[/green]")
    
    def quick_clone(self, target_url: str, output_dir: str = None):
        """Quick clone with limited depth."""
        self.config['max_depth'] = 1
        self.config['max_pages'] = 10
        self.clone_website(target_url, output_dir)
    
    def full_clone(self, target_url: str, output_dir: str = None):
        """Full clone with maximum depth."""
        self.config['max_depth'] = 5
        self.config['max_pages'] = 100
        self.clone_website(target_url, output_dir)
    
    def list_cloned_sites(self):
        """List all cloned websites."""
        cloned_dirs = [d for d in self.cloned_sites_dir.iterdir() if d.is_dir()]
        
        if not cloned_dirs:
            console.print("[yellow]No cloned websites found.[/yellow]")
            return
        
        table = Table(title="🌐 Cloned Websites", border_style="blue")
        table.add_column("Website", style="cyan")
        table.add_column("Pages", style="green")
        table.add_column("Date", style="yellow")
        
        for site_dir in sorted(cloned_dirs, key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                html_files = len(list(site_dir.glob("*.html")))
                date = time.strftime('%Y-%m-%d', time.localtime(site_dir.stat().st_mtime))
                
                table.add_row(site_dir.name, str(html_files), date)
            except Exception:
                table.add_row(site_dir.name, "Error", "Error")
        
        console.print(table)
