# core/devops_tools.py
import os
import json
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class DevOpsTools:
    """DevOps automation tools for CI/CD, monitoring, and infrastructure."""
    
    def __init__(self):
        self.templates_dir = Path("devops_templates")
        self.templates_dir.mkdir(exist_ok=True)
        self._create_templates()
    
    def _create_templates(self):
        """Create default DevOps templates."""
        # GitHub Actions template
        github_actions = """name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python -m pytest
    - name: Code quality check
      run: |
        pip install flake8 black
        flake8 .
        black --check .

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    - name: Deploy to production
      run: |
        echo "Deploying to production..."
"""
        
        # Docker template
        dockerfile = """FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "app.py"]
"""
        
        # Docker Compose template
        docker_compose = """version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./data:/app/data
  
  monitoring:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring:/etc/prometheus
"""
        
        # Prometheus config
        prometheus_config = """global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'python-app'
    static_configs:
      - targets: ['localhost:8000']
"""
        
        # Save templates
        (self.templates_dir / "github-actions.yml").write_text(github_actions)
        (self.templates_dir / "Dockerfile").write_text(dockerfile)
        (self.templates_dir / "docker-compose.yml").write_text(docker_compose)
        (self.templates_dir / "prometheus.yml").write_text(prometheus_config)
    
    def setup_github_actions(self, project_name: str = None):
        """Set up GitHub Actions CI/CD pipeline."""
        if not project_name:
            project_name = Path.cwd().name
        
        workflows_dir = Path(".github/workflows")
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        template = (self.templates_dir / "github-actions.yml").read_text()
        workflow_file = workflows_dir / "ci-cd.yml"
        workflow_file.write_text(template)
        
        console.print(f"[green]✅ GitHub Actions pipeline created: {workflow_file}[/green]")
        console.print(f"[cyan]Push to GitHub to trigger the pipeline![/cyan]")
    
    def setup_docker(self, project_name: str = None):
        """Set up Docker containerization."""
        if not project_name:
            project_name = Path.cwd().name
        
        dockerfile = self.templates_dir / "Dockerfile"
        docker_compose = self.templates_dir / "docker-compose.yml"
        
        # Copy templates to project root
        Path("Dockerfile").write_text(dockerfile.read_text())
        Path("docker-compose.yml").write_text(docker_compose.read_text())
        
        console.print(f"[green]✅ Docker setup complete for {project_name}[/green]")
        console.print(f"[cyan]Run 'docker build -t {project_name} .' to build[/cyan]")
        console.print(f"[cyan]Run 'docker-compose up' to start services[/cyan]")
    
    def setup_monitoring(self):
        """Set up Prometheus monitoring."""
        monitoring_dir = Path("monitoring")
        monitoring_dir.mkdir(exist_ok=True)
        
        prometheus_config = self.templates_dir / "prometheus.yml"
        (monitoring_dir / "prometheus.yml").write_text(prometheus_config.read_text())
        
        console.print(f"[green]✅ Prometheus monitoring configured[/green]")
        console.print(f"[cyan]Access metrics at: http://localhost:9090[/cyan]")
    
    def setup_logging(self, log_level: str = "INFO"):
        """Set up centralized logging system."""
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                },
            },
            "handlers": {
                "default": {
                    "level": log_level,
                    "formatter": "standard",
                    "class": "logging.StreamHandler",
                },
                "file": {
                    "level": log_level,
                    "formatter": "standard",
                    "class": "logging.FileHandler",
                    "filename": "logs/app.log",
                    "mode": "a",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default", "file"],
                    "level": log_level,
                    "propagate": False
                }
            }
        }
        
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        config_file = Path("logging_config.json")
        config_file.write_text(json.dumps(logging_config, indent=2))
        
        console.print(f"[green]✅ Logging system configured[/green]")
        console.print(f"[cyan]Logs will be written to: logs/app.log[/cyan]")
    
    def create_backup_system(self, source_dirs: list = None, backup_dir: str = "backups"):
        """Set up automated backup system."""
        if not source_dirs:
            source_dirs = [".", "data", "config"]
        
        backup_script = f"""#!/bin/bash
# Automated backup script
BACKUP_DIR="{backup_dir}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Create backup archive
tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" {' '.join(source_dirs)}

# Keep only last 10 backups
cd $BACKUP_DIR
ls -t backup_*.tar.gz | tail -n +11 | xargs -r rm

echo "Backup completed: backup_$TIMESTAMP.tar.gz"
"""
        
        backup_file = Path("backup.sh")
        backup_file.write_text(backup_script)
        backup_file.chmod(0o755)
        
        console.print(f"[green]✅ Backup system created: {backup_file}[/green]")
        console.print(f"[cyan]Run './backup.sh' to create backup[/cyan]")
        console.print(f"[cyan]Add to crontab for automated backups[/cyan]")
    
    def setup_load_testing(self, target_url: str = "http://localhost:8000"):
        """Set up load testing with Locust."""
        locust_file = f"""from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def index_page(self):
        self.client.get("/")
    
    @task(2)
    def api_endpoint(self):
        self.client.get("/api/health")
    
    @task(1)
    def heavy_operation(self):
        self.client.post("/api/process", json={{'data': 'test'}})
"""
        
        locust_config = Path("locustfile.py")
        locust_config.write_text(locust_file)
        
        requirements_add = """
# Load testing dependencies
locust>=2.15.0
"""
        
        # Append to requirements.txt if it exists
        req_file = Path("requirements.txt")
        if req_file.exists():
            with open(req_file, "a") as f:
                f.write(requirements_add)
        
        console.print(f"[green]✅ Load testing setup complete[/green]")
        console.print(f"[cyan]Install: pip install locust[/cyan]")
        console.print(f"[cyan]Run: locust -f locustfile.py --host={target_url}[/cyan]")
    
    def list_templates(self):
        """List available DevOps templates."""
        templates = list(self.templates_dir.glob("*.yml")) + list(self.templates_dir.glob("*.py"))
        
        table = Table(title="📋 Available DevOps Templates", border_style="blue")
        table.add_column("Template", style="cyan")
        table.add_column("Description", style="yellow")
        
        for template in templates:
            name = template.name
            if "github-actions" in name:
                desc = "CI/CD pipeline for GitHub"
            elif "Dockerfile" in name:
                desc = "Docker containerization"
            elif "docker-compose" in name:
                desc = "Multi-service orchestration"
            elif "prometheus" in name:
                desc = "Monitoring configuration"
            else:
                desc = "DevOps template"
            
            table.add_row(name, desc)
        
        console.print(table)
