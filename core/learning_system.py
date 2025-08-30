# core/learning_system.py
import sqlite3
import datetime
from pathlib import Path
from rich.console import Console

console = Console()

class LearningSystem:
    """
    Manages the AI's ability to learn from interactions, track performance,
    and suggest improvements.
    """
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initializes the SQLite database and creates necessary tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Table to store every user interaction
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        user_input TEXT NOT NULL,
                        ai_response TEXT,
                        model_used TEXT,
                        task_type TEXT,
                        response_time REAL,
                        was_successful INTEGER,
                        user_feedback INTEGER, -- e.g., 1-5 rating
                        error_message TEXT
                    )
                ''')
                # Table to track the performance of different models on different tasks
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS model_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_name TEXT NOT NULL,
                        task_type TEXT NOT NULL,
                        success_count INTEGER DEFAULT 0,
                        failure_count INTEGER DEFAULT 0,
                        total_requests INTEGER DEFAULT 0,
                        avg_response_time REAL DEFAULT 0.0,
                        UNIQUE(model_name, task_type)
                    )
                ''')
                conn.commit()
        except sqlite3.Error as e:
            console.print(f"[bold red]Database Error in LearningSystem: {e}[/bold red]")

    def record_interaction(self, user_input, ai_response, model_used, task_type, response_time, was_successful, error_message=None):
        """Records a single interaction between the user and the AI."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO interactions (timestamp, user_input, ai_response, model_used, task_type, response_time, was_successful, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (datetime.datetime.now().isoformat(), user_input, ai_response, model_used, task_type, response_time, 1 if was_successful else 0, error_message))
                conn.commit()
                self.update_model_performance(model_used, task_type, was_successful, response_time)
        except sqlite3.Error as e:
            console.print(f"[bold red]Error recording interaction: {e}[/bold red]")

    def update_model_performance(self, model_name, task_type, was_successful, response_time):
        """Updates the aggregated performance statistics for a given model and task type."""
        if not model_name or model_name == "Error":
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT success_count, failure_count, total_requests, avg_response_time FROM model_performance WHERE model_name = ? AND task_type = ?", (model_name, task_type))
                row = cursor.fetchone()

                if row:
                    success_count, failure_count, total_requests, avg_time = row
                    total_requests += 1
                    # Update running average for response time
                    new_avg_time = ((avg_time * (total_requests - 1)) + response_time) / total_requests
                    if was_successful:
                        success_count += 1
                    else:
                        failure_count += 1
                    
                    cursor.execute('''
                        UPDATE model_performance
                        SET success_count = ?, failure_count = ?, total_requests = ?, avg_response_time = ?
                        WHERE model_name = ? AND task_type = ?
                    ''', (success_count, failure_count, total_requests, new_avg_time, model_name, task_type))
                else:
                    # First record for this combination
                    success_count = 1 if was_successful else 0
                    failure_count = 1 if not was_successful else 0
                    cursor.execute('''
                        INSERT INTO model_performance (model_name, task_type, success_count, failure_count, total_requests, avg_response_time)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (model_name, task_type, success_count, failure_count, 1, response_time))
                conn.commit()
        except sqlite3.Error as e:
            console.print(f"[bold red]Error updating model performance: {e}[/bold red]")

    def get_best_model_for_task(self, task_type: str) -> str:
        """
        Retrieves the best-performing model for a specific task type based on historical data.
        The "best" model is the one with the highest success rate, with ties broken by faster response time.
        A minimum number of requests is required to ensure the data is statistically significant.
        """
        min_requests_threshold = 5 # Don't make a decision without at least 5 data points
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    SELECT model_name
                    FROM model_performance
                    WHERE task_type = ? AND total_requests >= ?
                    ORDER BY (CAST(success_count AS REAL) / total_requests) DESC, avg_response_time ASC
                    LIMIT 1
                ''', (task_type, min_requests_threshold))
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            console.print(f"[bold red]Error getting best model: {e}[/bold red]")
            return None

    def get_performance_report(self) -> str:
        """Generates a human-readable report of model performance."""
        report = "[bold cyan]🧠 AI Performance Report[/bold cyan]\n"
        report += "---------------------------\n"
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT model_name, task_type, success_count, total_requests, avg_response_time FROM model_performance ORDER BY model_name, task_type")
                rows = cursor.fetchall()

                if not rows:
                    return "No performance data recorded yet."

                for row in rows:
                    model, task, successes, total, avg_time = row
                    success_rate = (successes / total * 100) if total > 0 else 0
                    report += (
                        f"[bold]{model}[/] on [yellow]{task}[/yellow] tasks:\n"
                        f"  - Success Rate: {success_rate:.2f}% ({successes}/{total})\n"
                        f"  - Avg. Response Time: {avg_time:.3f}s\n\n"
                    )
            return report
        except sqlite3.Error as e:
            return f"[bold red]Could not generate performance report: {e}[/bold red]"


