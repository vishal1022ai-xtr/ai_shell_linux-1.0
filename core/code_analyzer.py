# core/code_analyzer.py
import ast
import re
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
import subprocess
import tempfile

console = Console()

class CodeAnalyzer:
    """Comprehensive code analysis with AI-powered insights."""
    
    def __init__(self, ai_manager):
        self.ai_manager = ai_manager
        self.analysis_results = {}
        
        # Common code issues patterns
        self.bug_patterns = {
            'unused_imports': r'^import\s+\w+$|^from\s+\w+\s+import\s+\w+$',
            'unused_variables': r'^\s*\w+\s*=\s*[^#\n]+$',
            'hardcoded_values': r'["\']\d{4,}["\']|["\']https?://[^"\']+["\']',
            'missing_docstrings': r'^def\s+\w+\([^)]*\):\s*$',
            'long_functions': r'^def\s+\w+\([^)]*\):\s*$',
            'complex_conditions': r'if\s+[^:]+and\s+[^:]+and\s+[^:]+:',
            'nested_loops': r'for\s+[^:]+:\s*\n\s*for\s+[^:]+:',
            'magic_numbers': r'\b\d{2,}\b(?!\s*[a-zA-Z])',
            'print_statements': r'print\s*\(',
            'bare_except': r'except\s*:',
            'global_variables': r'^global\s+\w+',
        }
        
        self.security_patterns = {
            'sql_injection': r'execute\s*\(\s*[\'"][^\'"]*\+',
            'command_injection': r'os\.system\s*\(|subprocess\.call\s*\(',
            'file_path_traversal': r'\.\./|\.\.\\',
            'hardcoded_secrets': r'password\s*=\s*["\'][^"\']+["\']|api_key\s*=\s*["\'][^"\']+["\']',
            'insecure_random': r'random\.randint\s*\(',
            'eval_usage': r'eval\s*\(',
            'exec_usage': r'exec\s*\(',
            'pickle_usage': r'pickle\.loads\s*\(',
            'xml_parsing': r'xml\.etree\.ElementTree\.parse\s*\(',
            'yaml_unsafe': r'yaml\.load\s*\(',
        }
        
        self.performance_patterns = {
            'inefficient_loops': r'for\s+\w+\s+in\s+range\s*\(\s*len\s*\(',
            'list_comprehension_opportunity': r'for\s+\w+\s+in\s+\w+:\s*\n\s*\w+\.append\s*\(',
            'string_concatenation': r'[\'"][^\'"]*\+[\'"][^\'"]*\+',
            'unnecessary_calculations': r'for\s+\w+\s+in\s+\w+:\s*\n\s*if\s+\w+\s+in\s+\w+:',
            'memory_inefficient': r'list\s*\(\s*map\s*\(',
            'deep_copy_opportunity': r'copy\.deepcopy\s*\(',
            'regex_compilation': r're\.(search|match|findall)\s*\(',
            'file_operations_in_loop': r'for\s+[^:]+:\s*\n\s*with\s+open\s*\(',
        }
    
    def analyze_code_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single code file comprehensively."""
        console.print(f"[cyan]🔍 Analyzing code file: {file_path}[/cyan]")
        
        if not os.path.exists(file_path):
            return {"error": f"File {file_path} not found"}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'file_path': file_path,
                'file_size': len(content),
                'lines_of_code': len(content.splitlines()),
                'timestamp': time.time(),
                'bugs': self._detect_bugs(content),
                'security_issues': self._detect_security_issues(content),
                'performance_issues': self._detect_performance_issues(content),
                'code_quality': self._analyze_code_quality(content),
                'ai_recommendations': self._get_ai_recommendations(content, file_path)
            }
            
            self.analysis_results[file_path] = analysis
            return analysis
            
        except Exception as e:
            return {"error": f"Failed to analyze {file_path}: {str(e)}"}
    
    def _detect_bugs(self, content: str) -> List[Dict[str, Any]]:
        """Detect potential bugs in the code."""
        bugs = []
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            for bug_type, pattern in self.bug_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    bugs.append({
                        'type': bug_type,
                        'line': i,
                        'code': line.strip(),
                        'severity': self._get_bug_severity(bug_type),
                        'description': self._get_bug_description(bug_type)
                    })
        
        return bugs
    
    def _detect_security_issues(self, content: str) -> List[Dict[str, Any]]:
        """Detect security vulnerabilities in the code."""
        security_issues = []
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            for issue_type, pattern in self.security_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    security_issues.append({
                        'type': issue_type,
                        'line': i,
                        'code': line.strip(),
                        'severity': 'HIGH',
                        'description': self._get_security_description(issue_type),
                        'mitigation': self._get_security_mitigation(issue_type)
                    })
        
        return security_issues
    
    def _detect_performance_issues(self, content: str) -> List[Dict[str, Any]]:
        """Detect performance optimization opportunities."""
        performance_issues = []
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            for issue_type, pattern in self.performance_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    performance_issues.append({
                        'type': issue_type,
                        'line': i,
                        'code': line.strip(),
                        'severity': 'MEDIUM',
                        'description': self._get_performance_description(issue_type),
                        'optimization': self._get_performance_optimization(issue_type)
                    })
        
        return performance_issues
    
    def _analyze_code_quality(self, content: str) -> Dict[str, Any]:
        """Analyze overall code quality metrics."""
        try:
            tree = ast.parse(content)
            
            # Count different types of nodes
            functions = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
            classes = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
            imports = len([node for node in ast.walk(tree) if isinstance(node, ast.Import)])
            imports_from = len([node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)])
            
            # Calculate complexity
            complexity = 0
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                    complexity += 1
            
            return {
                'functions': functions,
                'classes': classes,
                'imports': imports + imports_from,
                'complexity': complexity,
                'maintainability_index': max(0, 100 - complexity * 2),
                'lines_per_function': len(content.splitlines()) / max(functions, 1)
            }
        except SyntaxError:
            return {"error": "Syntax error in code"}
    
    def _get_ai_recommendations(self, content: str, file_path: str) -> List[str]:
        """Get AI-powered code improvement recommendations."""
        try:
            prompt = f"""
            Analyze this Python code and provide 3-5 specific, actionable recommendations for improvement:
            
            File: {file_path}
            Code:
            {content[:2000]}  # Limit to first 2000 chars for efficiency
            
            Focus on:
            1. Code quality and best practices
            2. Performance optimizations
            3. Security improvements
            4. Maintainability enhancements
            
            Provide specific, actionable recommendations with examples.
            """
            
            response, model_used = self.ai_manager.get_ai_response(prompt, model_preference='gemini')
            
            # Extract recommendations
            recommendations = []
            lines = response.split('\n')
            for line in lines:
                if line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '-', '•')):
                    recommendations.append(line.strip())
            
            return recommendations[:5]  # Limit to 5 recommendations
            
        except Exception as e:
            return [f"Could not generate AI recommendations: {str(e)}"]
    
    def _get_bug_severity(self, bug_type: str) -> str:
        """Get severity level for a bug type."""
        high_severity = ['unused_imports', 'bare_except', 'global_variables']
        medium_severity = ['unused_variables', 'missing_docstrings', 'print_statements']
        
        if bug_type in high_severity:
            return 'HIGH'
        elif bug_type in medium_severity:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _get_bug_description(self, bug_type: str) -> str:
        """Get description for a bug type."""
        descriptions = {
            'unused_imports': 'Unused import statement that can be removed',
            'unused_variables': 'Variable defined but never used',
            'hardcoded_values': 'Magic numbers or hardcoded values should be constants',
            'missing_docstrings': 'Function missing documentation string',
            'long_functions': 'Function is too long and should be split',
            'complex_conditions': 'Complex conditional logic that can be simplified',
            'nested_loops': 'Nested loops that may impact performance',
            'magic_numbers': 'Magic numbers should be named constants',
            'print_statements': 'Print statements should be replaced with proper logging',
            'bare_except': 'Bare except clause catches all exceptions',
            'global_variables': 'Global variables can make code harder to test'
        }
        return descriptions.get(bug_type, 'Potential code issue detected')
    
    def _get_security_description(self, issue_type: str) -> str:
        """Get description for a security issue."""
        descriptions = {
            'sql_injection': 'Potential SQL injection vulnerability',
            'command_injection': 'Command injection risk from user input',
            'file_path_traversal': 'Path traversal vulnerability possible',
            'hardcoded_secrets': 'Hardcoded secrets in source code',
            'insecure_random': 'Insecure random number generation',
            'eval_usage': 'Dangerous eval() function usage',
            'exec_usage': 'Dangerous exec() function usage',
            'pickle_usage': 'Unsafe pickle deserialization',
            'xml_parsing': 'XML parsing without security considerations',
            'yaml_unsafe': 'Unsafe YAML loading'
        }
        return descriptions.get(issue_type, 'Security vulnerability detected')
    
    def _get_security_mitigation(self, issue_type: str) -> str:
        """Get mitigation strategy for a security issue."""
        mitigations = {
            'sql_injection': 'Use parameterized queries or ORM',
            'command_injection': 'Validate and sanitize all user inputs',
            'file_path_traversal': 'Use os.path.abspath() and validate paths',
            'hardcoded_secrets': 'Use environment variables or secure vaults',
            'insecure_random': 'Use secrets module for cryptographic operations',
            'eval_usage': 'Avoid eval(), use safer alternatives',
            'exec_usage': 'Avoid exec(), use safer alternatives',
            'pickle_usage': 'Use json or other safe serialization',
            'xml_parsing': 'Use defusedxml or disable external entities',
            'yaml_unsafe': 'Use yaml.safe_load() instead'
        }
        return mitigations.get(issue_type, 'Review and fix security issue')
    
    def _get_performance_description(self, issue_type: str) -> str:
        """Get description for a performance issue."""
        descriptions = {
            'inefficient_loops': 'Inefficient loop structure',
            'list_comprehension_opportunity': 'List comprehension could improve performance',
            'string_concatenation': 'String concatenation in loops is inefficient',
            'unnecessary_calculations': 'Repeated calculations in loops',
            'memory_inefficient': 'Memory-inefficient operation',
            'deep_copy_opportunity': 'Deep copy may not be necessary',
            'regex_compilation': 'Regex compilation in loops',
            'file_operations_in_loop': 'File operations in loops'
        }
        return descriptions.get(issue_type, 'Performance optimization opportunity')
    
    def _get_performance_optimization(self, issue_type: str) -> str:
        """Get optimization suggestion for a performance issue."""
        optimizations = {
            'inefficient_loops': 'Use enumerate() or direct iteration',
            'list_comprehension_opportunity': 'Convert to list comprehension',
            'string_concatenation': 'Use join() or f-strings',
            'unnecessary_calculations': 'Move calculations outside loops',
            'memory_inefficient': 'Use generators or iterators',
            'deep_copy_opportunity': 'Use shallow copy if possible',
            'regex_compilation': 'Compile regex outside loops',
            'file_operations_in_loop': 'Batch file operations'
        }
        return optimizations.get(issue_type, 'Review for optimization opportunities')
    
    def generate_report(self, file_path: str = None) -> str:
        """Generate a comprehensive analysis report."""
        if file_path and file_path in self.analysis_results:
            analysis = self.analysis_results[file_path]
        elif file_path:
            analysis = self.analyze_code_file(file_path)
        else:
            # Generate report for all analyzed files
            if not self.analysis_results:
                return "No files analyzed yet."
            
            report = "# Code Analysis Report\n\n"
            for fp, result in self.analysis_results.items():
                report += f"## {fp}\n"
                report += self._format_analysis_result(result)
                report += "\n---\n\n"
            return report
        
        return self._format_analysis_result(analysis)
    
    def _format_analysis_result(self, analysis: Dict[str, Any]) -> str:
        """Format analysis results into a readable report."""
        if 'error' in analysis:
            return f"Error: {analysis['error']}"
        
        report = f"# Code Analysis Report for {analysis['file_path']}\n\n"
        report += f"**File Size:** {analysis['file_size']} bytes\n"
        report += f"**Lines of Code:** {analysis['lines_of_code']}\n"
        report += f"**Analysis Time:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(analysis['timestamp']))}\n\n"
        
        # Code Quality
        quality = analysis['code_quality']
        if 'error' not in quality:
            report += "## Code Quality Metrics\n\n"
            report += f"- **Functions:** {quality['functions']}\n"
            report += f"- **Classes:** {quality['classes']}\n"
            report += f"- **Imports:** {quality['imports']}\n"
            report += f"- **Complexity:** {quality['complexity']}\n"
            report += f"- **Maintainability Index:** {quality['maintainability_index']}/100\n"
            report += f"- **Lines per Function:** {quality['lines_per_function']:.1f}\n\n"
        
        # Bugs
        if analysis['bugs']:
            report += "## Bug Detection\n\n"
            for bug in analysis['bugs']:
                report += f"### {bug['type'].replace('_', ' ').title()} (Line {bug['line']})\n"
                report += f"**Severity:** {bug['severity']}\n"
                report += f"**Code:** `{bug['code']}`\n"
                report += f"**Description:** {bug['description']}\n\n"
        
        # Security Issues
        if analysis['security_issues']:
            report += "## Security Issues\n\n"
            for issue in analysis['security_issues']:
                report += f"### {issue['type'].replace('_', ' ').title()} (Line {issue['line']})\n"
                report += f"**Severity:** {issue['severity']}\n"
                report += f"**Code:** `{issue['code']}`\n"
                report += f"**Description:** {issue['description']}\n"
                report += f"**Mitigation:** {issue['mitigation']}\n\n"
        
        # Performance Issues
        if analysis['performance_issues']:
            report += "## Performance Issues\n\n"
            for issue in analysis['performance_issues']:
                report += f"### {issue['type'].replace('_', ' ').title()} (Line {issue['line']})\n"
                report += f"**Severity:** {issue['severity']}\n"
                report += f"**Code:** `{issue['code']}`\n"
                report += f"**Description:** {issue['description']}\n"
                report += f"**Optimization:** {issue['optimization']}\n\n"
        
        # AI Recommendations
        if analysis['ai_recommendations']:
            report += "## AI-Powered Recommendations\n\n"
            for i, rec in enumerate(analysis['ai_recommendations'], 1):
                report += f"{i}. {rec}\n"
        
        return report
