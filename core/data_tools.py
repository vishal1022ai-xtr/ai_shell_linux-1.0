# core/data_tools.py
import json
import pandas as pd
import numpy as np
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

console = Console()

class DataTools:
    """Data science and analytics tools."""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.charts_dir = Path("charts")
        self.charts_dir.mkdir(exist_ok=True)
        
        # Set matplotlib style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def create_sample_data(self, data_type: str = "sales"):
        """Create sample datasets for demonstration."""
        if data_type == "sales":
            dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
            np.random.seed(42)
            
            data = {
                'date': dates,
                'sales': np.random.normal(1000, 200, len(dates)),
                'customers': np.random.poisson(50, len(dates)),
                'product_id': np.random.choice(['A', 'B', 'C'], len(dates)),
                'region': np.random.choice(['North', 'South', 'East', 'West'], len(dates))
            }
            
            df = pd.DataFrame(data)
            df.to_csv(self.data_dir / "sample_sales.csv", index=False)
            console.print(f"[green]✅ Sample sales data created: {self.data_dir}/sample_sales.csv[/green]")
            return df
            
        elif data_type == "time_series":
            dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='M')
            np.random.seed(42)
            
            # Create trend and seasonality
            trend = np.linspace(100, 200, len(dates))
            seasonality = 20 * np.sin(2 * np.pi * np.arange(len(dates)) / 12)
            noise = np.random.normal(0, 10, len(dates))
            
            data = {
                'date': dates,
                'value': trend + seasonality + noise,
                'category': np.random.choice(['A', 'B'], len(dates))
            }
            
            df = pd.DataFrame(data)
            df.to_csv(self.data_dir / "sample_timeseries.csv", index=False)
            console.print(f"[green]✅ Sample time series data created: {self.data_dir}/sample_timeseries.csv[/green]")
            return df
    
    def create_visualization(self, data_file: str, chart_type: str = "line"):
        """Create various types of charts and visualizations."""
        file_path = self.data_dir / data_file
        
        if not file_path.exists():
            console.print(f"[red]Data file not found: {file_path}[/red]")
            return
        
        df = pd.read_csv(file_path)
        
        if chart_type == "line":
            self._create_line_chart(df, data_file)
        elif chart_type == "bar":
            self._create_bar_chart(df, data_file)
        elif chart_type == "scatter":
            self._create_scatter_chart(df, data_file)
        elif chart_type == "heatmap":
            self._create_heatmap(df, data_file)
        elif chart_type == "distribution":
            self._create_distribution_chart(df, data_file)
        else:
            console.print(f"[yellow]Unknown chart type: {chart_type}[/yellow]")
    
    def _create_line_chart(self, df: pd.DataFrame, filename: str):
        """Create line chart visualization."""
        plt.figure(figsize=(12, 6))
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols[:3]:  # Plot first 3 numeric columns
                plt.plot(df['date'], df[col], label=col, linewidth=2)
            
            plt.title(f'Time Series: {filename}', fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Value', fontsize=12)
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
        
        chart_path = self.charts_dir / f"{filename.replace('.csv', '')}_line.png"
        plt.tight_layout()
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        console.print(f"[green]✅ Line chart saved: {chart_path}[/green]")
    
    def _create_bar_chart(self, df: pd.DataFrame, filename: str):
        """Create bar chart visualization."""
        plt.figure(figsize=(10, 6))
        
        # Find categorical columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        if len(categorical_cols) > 0:
            col = categorical_cols[0]
            value_counts = df[col].value_counts()
            
            plt.bar(range(len(value_counts)), value_counts.values, 
                   color=sns.color_palette("husl", len(value_counts)))
            plt.title(f'Distribution: {col}', fontsize=16, fontweight='bold')
            plt.xlabel(col, fontsize=12)
            plt.ylabel('Count', fontsize=12)
            plt.xticks(range(len(value_counts)), value_counts.index, rotation=45)
        
        chart_path = self.charts_dir / f"{filename.replace('.csv', '')}_bar.png"
        plt.tight_layout()
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        console.print(f"[green]✅ Bar chart saved: {chart_path}[/green]")
    
    def _create_scatter_chart(self, df: pd.DataFrame, filename: str):
        """Create scatter plot visualization."""
        plt.figure(figsize=(10, 6))
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) >= 2:
            plt.scatter(df[numeric_cols[0]], df[numeric_cols[1]], alpha=0.6, s=50)
            plt.title(f'Scatter Plot: {numeric_cols[0]} vs {numeric_cols[1]}', 
                     fontsize=16, fontweight='bold')
            plt.xlabel(numeric_cols[0], fontsize=12)
            plt.ylabel(numeric_cols[1], fontsize=12)
            plt.grid(True, alpha=0.3)
        
        chart_path = self.charts_dir / f"{filename.replace('.csv', '')}_scatter.png"
        plt.tight_layout()
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        console.print(f"[green]✅ Scatter plot saved: {chart_path}[/green]")
    
    def _create_heatmap(self, df: pd.DataFrame, filename: str):
        """Create correlation heatmap."""
        plt.figure(figsize=(10, 8))
        
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) > 1:
            correlation_matrix = numeric_df.corr()
            
            sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                       square=True, linewidths=0.5)
            plt.title(f'Correlation Heatmap: {filename}', fontsize=16, fontweight='bold')
        
        chart_path = self.charts_dir / f"{filename.replace('.csv', '')}_heatmap.png"
        plt.tight_layout()
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        console.print(f"[green]✅ Heatmap saved: {chart_path}[/green]")
    
    def _create_distribution_chart(self, df: pd.DataFrame, filename: str):
        """Create distribution/histogram visualization."""
        plt.figure(figsize=(12, 6))
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 0:
            col = numeric_cols[0]
            plt.hist(df[col], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
            plt.title(f'Distribution: {col}', fontsize=16, fontweight='bold')
            plt.xlabel(col, fontsize=12)
            plt.ylabel('Frequency', fontsize=12)
            plt.grid(True, alpha=0.3)
        
        chart_path = self.charts_dir / f"{filename.replace('.csv', '')}_distribution.png"
        plt.tight_layout()
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        console.print(f"[green]✅ Distribution chart saved: {chart_path}[/green]")
    
    def create_etl_pipeline(self, source_file: str, transformations: list = None):
        """Create ETL (Extract, Transform, Load) pipeline."""
        source_path = self.data_dir / source_file
        
        if not source_path.exists():
            console.print(f"[red]Source file not found: {source_path}[/red]")
            return
        
        # Extract
        df = pd.read_csv(source_path)
        console.print(f"[cyan]📊 Extracted {len(df)} rows from {source_file}[/cyan]")
        
        # Transform
        if transformations:
            for transform in transformations:
                if transform == "clean_missing":
                    df = df.dropna()
                    console.print(f"[cyan]🧹 Cleaned missing values: {len(df)} rows remaining[/cyan]")
                elif transform == "remove_duplicates":
                    initial_count = len(df)
                    df = df.drop_duplicates()
                    console.print(f"[cyan]🔄 Removed {initial_count - len(df)} duplicates[/cyan]")
                elif transform == "normalize":
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    for col in numeric_cols:
                        df[col] = (df[col] - df[col].mean()) / df[col].std()
                    console.print(f"[cyan]📏 Normalized numeric columns[/cyan]")
        
        # Load
        output_file = f"processed_{source_file}"
        output_path = self.data_dir / output_file
        df.to_csv(output_path, index=False)
        
        console.print(f"[green]✅ ETL pipeline completed: {output_file}[/green]")
        console.print(f"[cyan]📈 Data shape: {df.shape}[/cyan]")
        
        return df
    
    def create_predictive_model(self, data_file: str, target_column: str = None):
        """Create simple predictive model using linear regression."""
        try:
            from sklearn.linear_model import LinearRegression
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import mean_squared_error, r2_score
        except ImportError:
            console.print("[red]scikit-learn not installed. Install with: pip install scikit-learn[/red]")
            return
        
        file_path = self.data_dir / data_file
        
        if not file_path.exists():
            console.print(f"[red]Data file not found: {file_path}[/red]")
            return
        
        df = pd.read_csv(file_path)
        numeric_df = df.select_dtypes(include=[np.number])
        
        if target_column and target_column in numeric_df.columns:
            y = numeric_df[target_column]
            X = numeric_df.drop(columns=[target_column])
        else:
            # Use last column as target
            y = numeric_df.iloc[:, -1]
            X = numeric_df.iloc[:, :-1]
        
        if len(X.columns) == 0:
            console.print("[red]No numeric features found for prediction[/red]")
            return
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train model
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        
        # Evaluate
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Save model info
        model_info = {
            'model_type': 'LinearRegression',
            'features': list(X.columns),
            'target': y.name if hasattr(y, 'name') else 'target',
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'mean_squared_error': mse,
            'r2_score': r2,
            'coefficients': dict(zip(X.columns, model.coef_)),
            'intercept': float(model.intercept_)
        }
        
        model_file = self.data_dir / f"model_{data_file.replace('.csv', '')}.json"
        with open(model_file, 'w') as f:
            json.dump(model_info, f, indent=2)
        
        console.print(f"[green]✅ Predictive model created and saved: {model_file}[/green]")
        console.print(f"[cyan]📊 Model Performance:[/cyan]")
        console.print(f"[cyan]   R² Score: {r2:.4f}[/cyan]")
        console.print(f"[cyan]   MSE: {mse:.4f}[/cyan]")
        
        return model_info
    
    def create_dashboard(self, data_files: list = None):
        """Create a simple HTML dashboard with charts."""
        if not data_files:
            data_files = [f.name for f in self.data_dir.glob("*.csv")]
        
        dashboard_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                 color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .chart-container { background: white; padding: 20px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .chart { text-align: center; margin: 20px 0; }
        .chart img { max-width: 100%; height: auto; border-radius: 5px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .stat-value { font-size: 2em; font-weight: bold; color: #667eea; }
        .stat-label { color: #666; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Data Analytics Dashboard</h1>
        <p>Generated on """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
    </div>
"""
        
        # Add charts
        chart_files = list(self.charts_dir.glob("*.png"))
        for chart_file in chart_files:
            dashboard_html += f"""
    <div class="chart-container">
        <h3>{chart_file.stem.replace('_', ' ').title()}</h3>
        <div class="chart">
            <img src="charts/{chart_file.name}" alt="{chart_file.stem}">
        </div>
    </div>
"""
        
        # Add data summary
        dashboard_html += """
    <div class="chart-container">
        <h3>📈 Data Summary</h3>
        <div class="stats">
"""
        
        for data_file in data_files:
            try:
                df = pd.read_csv(self.data_dir / data_file)
                dashboard_html += f"""
            <div class="stat-card">
                <div class="stat-value">{len(df):,}</div>
                <div class="stat-label">Rows in {data_file}</div>
            </div>
"""
            except:
                pass
        
        dashboard_html += """
        </div>
    </div>
</body>
</html>
"""
        
        dashboard_path = Path("dashboard.html")
        dashboard_path.write_text(dashboard_html)
        
        console.print(f"[green]✅ Dashboard created: {dashboard_path}[/green]")
        console.print(f"[cyan]Open dashboard.html in your browser to view[/cyan]")
        
        return dashboard_path
    
    def list_datasets(self):
        """List available datasets and their information."""
        csv_files = list(self.data_dir.glob("*.csv"))
        
        if not csv_files:
            console.print("[yellow]No datasets found. Use create_sample_data() to generate sample data.[/yellow]")
            return
        
        table = Table(title="📊 Available Datasets", border_style="blue")
        table.add_column("Dataset", style="cyan")
        table.add_column("Rows", style="green")
        table.add_column("Columns", style="yellow")
        table.add_column("Size", style="magenta")
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                size_kb = csv_file.stat().st_size / 1024
                table.add_row(
                    csv_file.name,
                    str(len(df)),
                    str(len(df.columns)),
                    f"{size_kb:.1f} KB"
                )
            except Exception as e:
                table.add_row(csv_file.name, "Error", "Error", "Error")
        
        console.print(table)
