# core/ethical_hacking.py
import socket
import subprocess
import requests
import dns.resolver
import whois
import ssl
import json
import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from urllib.parse import urlparse, urljoin
import threading
import queue

console = Console()

class EthicalHackingSuite:
    """Comprehensive ethical hacking toolkit for security professionals."""
    
    def __init__(self):
        self.results_dir = Path("security_reports")
        self.results_dir.mkdir(exist_ok=True)
        self.scan_results = {}
        self.current_scan = None
        
        # Common ports for scanning
        self.common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 1723, 3306, 3389, 5900, 8080]
        
        # Vulnerability patterns
        self.vuln_patterns = {
            'sql_injection': [
                "' OR '1'='1",
                "'; DROP TABLE users; --",
                "' UNION SELECT * FROM users --",
                "admin'--",
                "1' OR '1'='1'--"
            ],
            'xss': [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "javascript:alert('XSS')",
                "<svg onload=alert('XSS')>",
                "';alert('XSS');//"
            ],
            'csrf': [
                "csrf_token",
                "authenticity_token",
                "_token",
                "xsrf_token"
            ]
        }
    
    def start_security_assessment(self, target: str, scan_type: str = "full"):
        """Start a comprehensive security assessment."""
        console.print(f"[bold cyan]🔒 Starting Security Assessment[/bold cyan]")
        console.print(f"[cyan]Target: {target}[/cyan]")
        console.print(f"[cyan]Scan Type: {scan_type}[/cyan]")
        
        self.current_scan = {
            'target': target,
            'start_time': time.time(),
            'scan_type': scan_type,
            'results': {}
        }
        
        try:
            if scan_type in ["full", "recon"]:
                self._perform_reconnaissance(target)
            
            if scan_type in ["full", "vuln"]:
                self._perform_vulnerability_assessment(target)
            
            if scan_type in ["full", "web"]:
                self._perform_web_application_testing(target)
            
            if scan_type in ["full", "network"]:
                self._perform_network_security_testing(target)
            
            self._generate_security_report(target)
            
        except Exception as e:
            console.print(f"[red]❌ Security assessment failed: {e}[/red]")
        
        console.print(f"[green]✅ Security assessment completed![/green]")
    
    def _perform_reconnaissance(self, target: str):
        """Perform reconnaissance and information gathering."""
        console.print(f"[cyan]🔍 Performing Reconnaissance on {target}[/cyan]")
        
        recon_results = {
            'dns_info': self._dns_enumeration(target),
            'whois_info': self._whois_lookup(target),
            'subdomains': self._subdomain_enumeration(target),
            'ports': self._port_scanning(target),
            'technologies': self._technology_detection(target)
        }
        
        self.current_scan['results']['reconnaissance'] = recon_results
        console.print(f"[green]✅ Reconnaissance completed[/green]")
    
    def _dns_enumeration(self, target: str):
        """Perform DNS enumeration."""
        console.print(f"[cyan]  📡 DNS Enumeration...[/cyan]")
        
        dns_records = {}
        record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']
        
        for record_type in record_types:
            try:
                answers = dns.resolver.resolve(target, record_type)
                dns_records[record_type] = [str(answer) for answer in answers]
            except Exception:
                dns_records[record_type] = []
        
        return dns_records
    
    def _whois_lookup(self, target: str):
        """Perform WHOIS lookup."""
        console.print(f"[cyan]  📋 WHOIS Lookup...[/cyan]")
        
        try:
            w = whois.whois(target)
            return {
                'registrar': w.registrar,
                'creation_date': str(w.creation_date),
                'expiration_date': str(w.expiration_date),
                'name_servers': w.name_servers,
                'status': w.status
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _subdomain_enumeration(self, target: str):
        """Enumerate subdomains."""
        console.print(f"[cyan]  🌐 Subdomain Enumeration...[/cyan]")
        
        # Common subdomain wordlist
        common_subdomains = [
            'www', 'mail', 'ftp', 'admin', 'blog', 'dev', 'test', 'staging',
            'api', 'cdn', 'static', 'img', 'images', 'media', 'support',
            'help', 'docs', 'wiki', 'forum', 'shop', 'store', 'app'
        ]
        
        found_subdomains = []
        
        for subdomain in common_subdomains:
            full_domain = f"{subdomain}.{target}"
            try:
                socket.gethostbyname(full_domain)
                found_subdomains.append(full_domain)
            except socket.gaierror:
                continue
        
        return found_subdomains
    
    def _port_scanning(self, target: str):
        """Perform port scanning."""
        console.print(f"[cyan]  🔌 Port Scanning...[/cyan]")
        
        open_ports = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Scanning ports...", total=len(self.common_ports))
            
            for port in self.common_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((target, port))
                    if result == 0:
                        service = self._get_service_name(port)
                        open_ports.append({'port': port, 'service': service, 'state': 'open'})
                    sock.close()
                except Exception:
                    pass
                
                progress.advance(task)
        
        return open_ports
    
    def _get_service_name(self, port: int) -> str:
        """Get service name for common ports."""
        services = {
            21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS',
            80: 'HTTP', 110: 'POP3', 143: 'IMAP', 443: 'HTTPS', 993: 'IMAPS',
            995: 'POP3S', 1723: 'PPTP', 3306: 'MySQL', 3389: 'RDP',
            5900: 'VNC', 8080: 'HTTP-Proxy'
        }
        return services.get(port, 'Unknown')
    
    def _technology_detection(self, target: str):
        """Detect technologies used by the target."""
        console.print(f"[cyan]  🛠️ Technology Detection...[/cyan]")
        
        technologies = {}
        
        try:
            # Check HTTP headers
            if not target.startswith(('http://', 'https://')):
                target = f"http://{target}"
            
            response = requests.get(target, timeout=10, allow_redirects=True)
            headers = response.headers
            
            # Detect web server
            if 'Server' in headers:
                technologies['web_server'] = headers['Server']
            
            # Detect framework
            if 'X-Powered-By' in headers:
                technologies['framework'] = headers['X-Powered-By']
            
            # Detect security headers
            security_headers = ['X-Frame-Options', 'X-Content-Type-Options', 
                              'X-XSS-Protection', 'Strict-Transport-Security']
            technologies['security_headers'] = {h: headers.get(h, 'Not Set') for h in security_headers}
            
            # Check for common technologies in response
            content = response.text.lower()
            if 'wordpress' in content:
                technologies['cms'] = 'WordPress'
            elif 'drupal' in content:
                technologies['cms'] = 'Drupal'
            elif 'joomla' in content:
                technologies['cms'] = 'Joomla'
            
        except Exception as e:
            technologies['error'] = str(e)
        
        return technologies
    
    def _perform_vulnerability_assessment(self, target: str):
        """Perform vulnerability assessment."""
        console.print(f"[cyan]🔍 Performing Vulnerability Assessment[/cyan]")
        
        vuln_results = {
            'ssl_analysis': self._ssl_security_analysis(target),
            'open_ports_analysis': self._analyze_open_ports(target),
            'common_vulnerabilities': self._check_common_vulnerabilities(target)
        }
        
        self.current_scan['results']['vulnerability_assessment'] = vuln_results
        console.print(f"[green]✅ Vulnerability assessment completed[/green]")
    
    def _ssl_security_analysis(self, target: str):
        """Analyze SSL/TLS security."""
        console.print(f"[cyan]  🔐 SSL Security Analysis...[/cyan]")
        
        try:
            if not target.startswith(('http://', 'https://')):
                target = f"https://{target}"
            
            parsed_url = urlparse(target)
            context = ssl.create_default_context()
            
            with socket.create_connection((parsed_url.hostname, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=parsed_url.hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    return {
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'subject': dict(x[0] for x in cert['subject']),
                        'version': cert['version'],
                        'serial_number': cert['serialNumber'],
                        'not_before': cert['notBefore'],
                        'not_after': cert['notAfter'],
                        'cipher': ssock.cipher(),
                        'tls_version': ssock.version()
                    }
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_open_ports(self, target: str):
        """Analyze security implications of open ports."""
        console.print(f"[cyan]  🚨 Open Ports Security Analysis...[/cyan]")
        
        if 'reconnaissance' not in self.current_scan['results']:
            return {'error': 'Reconnaissance not performed yet'}
        
        open_ports = self.current_scan['results']['reconnaissance']['ports']
        security_analysis = []
        
        for port_info in open_ports:
            port = port_info['port']
            service = port_info['service']
            
            risk_level = 'LOW'
            recommendations = []
            
            if port in [21, 23]:  # FTP, Telnet
                risk_level = 'HIGH'
                recommendations.append('Disable unencrypted services')
                recommendations.append('Use SFTP/SSH instead')
            elif port == 22:  # SSH
                risk_level = 'MEDIUM'
                recommendations.append('Ensure SSH is properly configured')
                recommendations.append('Use key-based authentication')
            elif port == 80:  # HTTP
                risk_level = 'MEDIUM'
                recommendations.append('Redirect to HTTPS')
                recommendations.append('Implement security headers')
            elif port == 3389:  # RDP
                risk_level = 'HIGH'
                recommendations.append('Restrict RDP access')
                recommendations.append('Use VPN for remote access')
            
            security_analysis.append({
                'port': port,
                'service': service,
                'risk_level': risk_level,
                'recommendations': recommendations
            })
        
        return security_analysis
    
    def _check_common_vulnerabilities(self, target: str):
        """Check for common vulnerabilities."""
        console.print(f"[cyan]  🚨 Common Vulnerabilities Check...[/cyan]")
        
        vulnerabilities = []
        
        try:
            if not target.startswith(('http://', 'https://')):
                target = f"http://{target}"
            
            # Check for directory listing
            test_paths = ['/admin', '/backup', '/config', '/logs', '/tmp', '/upload']
            for path in test_paths:
                try:
                    response = requests.get(f"{target}{path}", timeout=5)
                    if response.status_code == 200 and 'Index of' in response.text:
                        vulnerabilities.append({
                            'type': 'Directory Listing',
                            'path': path,
                            'severity': 'MEDIUM',
                            'description': f'Directory listing enabled at {path}'
                        })
                except:
                    continue
            
            # Check for common files
            common_files = ['robots.txt', 'sitemap.xml', '.htaccess', 'web.config']
            for file in common_files:
                try:
                    response = requests.get(f"{target}/{file}", timeout=5)
                    if response.status_code == 200:
                        vulnerabilities.append({
                            'type': 'Information Disclosure',
                            'file': file,
                            'severity': 'LOW',
                            'description': f'Common file accessible: {file}'
                        })
                except:
                    continue
                    
        except Exception as e:
            vulnerabilities.append({
                'type': 'Error',
                'severity': 'UNKNOWN',
                'description': f'Error during vulnerability check: {str(e)}'
            })
        
        return vulnerabilities
    
    def _perform_web_application_testing(self, target: str):
        """Perform web application security testing."""
        console.print(f"[cyan]🌐 Performing Web Application Testing[/cyan]")
        
        web_results = {
            'input_validation': self._test_input_validation(target),
            'authentication': self._test_authentication(target),
            'session_management': self._test_session_management(target),
            'csrf_protection': self._test_csrf_protection(target)
        }
        
        self.current_scan['results']['web_application_testing'] = web_results
        console.print(f"[green]✅ Web application testing completed[/green]")
    
    def _test_input_validation(self, target: str):
        """Test input validation and injection vulnerabilities."""
        console.print(f"[cyan]  🧪 Input Validation Testing...[/cyan]")
        
        if not target.startswith(('http://', 'https://')):
            target = f"http://{target}"
        
        test_results = []
        
        # Test for SQL injection
        for payload in self.vuln_patterns['sql_injection']:
            try:
                response = requests.get(f"{target}/search?q={payload}", timeout=5)
                if any(error in response.text.lower() for error in ['sql', 'mysql', 'oracle', 'error']):
                    test_results.append({
                        'vulnerability': 'SQL Injection',
                        'payload': payload,
                        'severity': 'HIGH',
                        'evidence': 'SQL error in response'
                    })
            except:
                continue
        
        # Test for XSS
        for payload in self.vuln_patterns['xss']:
            try:
                response = requests.get(f"{target}/search?q={payload}", timeout=5)
                if payload in response.text:
                    test_results.append({
                        'vulnerability': 'Cross-Site Scripting (XSS)',
                        'payload': payload,
                        'severity': 'HIGH',
                        'evidence': 'XSS payload reflected in response'
                    })
            except:
                continue
        
        return test_results
    
    def _test_authentication(self, target: str):
        """Test authentication mechanisms."""
        console.print(f"[cyan]  🔑 Authentication Testing...[/cyan]")
        
        if not target.startswith(('http://', 'https://')):
            target = f"http://{target}"
        
        test_results = []
        
        # Test for default credentials
        default_creds = [
            ('admin', 'admin'),
            ('admin', 'password'),
            ('root', 'root'),
            ('test', 'test'),
            ('guest', 'guest')
        ]
        
        for username, password in default_creds:
            try:
                response = requests.post(f"{target}/login", 
                                      data={'username': username, 'password': password},
                                      timeout=5)
                if 'dashboard' in response.text.lower() or 'welcome' in response.text.lower():
                    test_results.append({
                        'vulnerability': 'Default Credentials',
                        'credentials': f'{username}:{password}',
                        'severity': 'HIGH',
                        'evidence': 'Successfully authenticated with default credentials'
                    })
            except:
                continue
        
        return test_results
    
    def _test_session_management(self, target: str):
        """Test session management security."""
        console.print(f"[cyan]  🎫 Session Management Testing...[/cyan]")
        
        if not target.startswith(('http://', 'https://')):
            target = f"http://{target}"
        
        test_results = []
        
        try:
            # Check for session fixation
            session1 = requests.Session()
            session2 = requests.Session()
            
            # Get initial session
            response1 = session1.get(target, timeout=5)
            session_id1 = session1.cookies.get_dict()
            
            # Get another session
            response2 = session2.get(target, timeout=5)
            session_id2 = session2.cookies.get_dict()
            
            if session_id1 == session_id2:
                test_results.append({
                    'vulnerability': 'Session Fixation',
                    'severity': 'MEDIUM',
                    'evidence': 'Same session ID assigned to different sessions'
                })
                
        except Exception as e:
            test_results.append({
                'vulnerability': 'Session Testing Error',
                'severity': 'UNKNOWN',
                'evidence': f'Error during session testing: {str(e)}'
            })
        
        return test_results
    
    def _test_csrf_protection(self, target: str):
        """Test CSRF protection."""
        console.print(f"[cyan]  🛡️ CSRF Protection Testing...[/cyan]")
        
        if not target.startswith(('http://', 'https://')):
            target = f"http://{target}"
        
        test_results = []
        
        try:
            # Check for CSRF tokens
            response = requests.get(target, timeout=5)
            content = response.text.lower()
            
            csrf_tokens_found = []
            for token_name in self.vuln_patterns['csrf']:
                if token_name in content:
                    csrf_tokens_found.append(token_name)
            
            if not csrf_tokens_found:
                test_results.append({
                    'vulnerability': 'Missing CSRF Protection',
                    'severity': 'MEDIUM',
                    'evidence': 'No CSRF tokens found in forms'
                })
            else:
                test_results.append({
                    'vulnerability': 'CSRF Protection Present',
                    'severity': 'INFO',
                    'evidence': f'CSRF tokens found: {", ".join(csrf_tokens_found)}'
                })
                
        except Exception as e:
            test_results.append({
                'vulnerability': 'CSRF Testing Error',
                'severity': 'UNKNOWN',
                'evidence': f'Error during CSRF testing: {str(e)}'
            })
        
        return test_results
    
    def _perform_network_security_testing(self, target: str):
        """Perform network security testing."""
        console.print(f"[cyan]🌐 Performing Network Security Testing[/cyan]")
        
        network_results = {
            'firewall_analysis': self._analyze_firewall(target),
            'network_traffic': self._analyze_network_traffic(target)
        }
        
        self.current_scan['results']['network_security_testing'] = network_results
        console.print(f"[green]✅ Network security testing completed[/green]")
    
    def _analyze_firewall(self, target: str):
        """Analyze firewall configuration."""
        console.print(f"[cyan]  🔥 Firewall Analysis...[/cyan]")
        
        # This is a simplified firewall analysis
        # In real scenarios, you'd use tools like nmap with various scan types
        
        return {
            'status': 'Basic analysis completed',
            'recommendation': 'Use nmap for comprehensive firewall testing'
        }
    
    def _analyze_network_traffic(self, target: str):
        """Analyze network traffic patterns."""
        console.print(f"[cyan]  📊 Network Traffic Analysis...[/cyan]")
        
        # This is a simplified traffic analysis
        # In real scenarios, you'd use tools like Wireshark or tcpdump
        
        return {
            'status': 'Basic analysis completed',
            'recommendation': 'Use packet capture tools for detailed traffic analysis'
        }
    
    def _generate_security_report(self, target: str):
        """Generate comprehensive security report."""
        console.print(f"[cyan]📋 Generating Security Report[/cyan]")
        
        if not self.current_scan:
            console.print("[red]No scan results to report[/red]")
            return
        
        report = self._format_security_report()
        
        # Save report to file
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = self.results_dir / f"security_report_{target}_{timestamp}.md"
        report_file.write_text(report)
        
        # Save raw results as JSON
        json_file = self.results_dir / f"security_results_{target}_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(self.current_scan, f, indent=2)
        
        console.print(f"[green]✅ Security report saved: {report_file}[/green]")
        console.print(f"[green]✅ Raw results saved: {json_file}[/green]")
        
        # Display summary
        self._display_security_summary()
    
    def _format_security_report(self) -> str:
        """Format security report in Markdown."""
        if not self.current_scan:
            return "No scan results available."
        
        scan = self.current_scan
        results = scan['results']
        
        report = f"""# Security Assessment Report

## Executive Summary
- **Target**: {scan['target']}
- **Scan Type**: {scan['scan_type']}
- **Date**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(scan['start_time']))}
- **Duration**: {time.time() - scan['start_time']:.2f} seconds

## Reconnaissance Results

### DNS Information
"""
        
        if 'reconnaissance' in results:
            recon = results['reconnaissance']
            
            # DNS Info
            if 'dns_info' in recon:
                report += "\n#### DNS Records\n"
                for record_type, records in recon['dns_info'].items():
                    if records:
                        report += f"- **{record_type}**: {', '.join(records)}\n"
            
            # WHOIS Info
            if 'whois_info' in recon:
                report += "\n#### WHOIS Information\n"
                whois_info = recon['whois_info']
                for key, value in whois_info.items():
                    if value and key != 'error':
                        report += f"- **{key}**: {value}\n"
            
            # Subdomains
            if 'subdomains' in recon and recon['subdomains']:
                report += f"\n#### Subdomains Found\n"
                for subdomain in recon['subdomains']:
                    report += f"- {subdomain}\n"
            
            # Open Ports
            if 'ports' in recon:
                report += "\n#### Open Ports\n"
                for port_info in recon['ports']:
                    report += f"- **Port {port_info['port']}**: {port_info['service']} ({port_info['state']})\n"
            
            # Technologies
            if 'technologies' in recon:
                report += "\n#### Technologies Detected\n"
                tech = recon['technologies']
                for key, value in tech.items():
                    if value and key != 'error':
                        report += f"- **{key}**: {value}\n"
        
        # Vulnerability Assessment
        if 'vulnerability_assessment' in results:
            report += "\n## Vulnerability Assessment\n"
            vuln = results['vulnerability_assessment']
            
            if 'ssl_analysis' in vuln:
                report += "\n### SSL/TLS Security\n"
                ssl_info = vuln['ssl_analysis']
                if 'error' not in ssl_info:
                    report += f"- **Issuer**: {ssl_info.get('issuer', {}).get('commonName', 'Unknown')}\n"
                    report += f"- **Valid Until**: {ssl_info.get('not_after', 'Unknown')}\n"
                    report += f"- **TLS Version**: {ssl_info.get('tls_version', 'Unknown')}\n"
            
            if 'open_ports_analysis' in vuln:
                report += "\n### Port Security Analysis\n"
                for port_analysis in vuln['open_ports_analysis']:
                    if 'error' not in port_analysis:
                        report += f"- **Port {port_analysis['port']}**: {port_analysis['risk_level']} risk - {port_analysis['service']}\n"
                        for rec in port_analysis['recommendations']:
                            report += f"  - {rec}\n"
        
        # Web Application Testing
        if 'web_application_testing' in results:
            report += "\n## Web Application Security\n"
            web = results['web_application_testing']
            
            for test_type, test_results in web.items():
                if test_results:
                    report += f"\n### {test_type.replace('_', ' ').title()}\n"
                    for result in test_results:
                        report += f"- **{result['vulnerability']}**: {result['severity']} severity\n"
                        report += f"  - Evidence: {result['evidence']}\n"
        
        # Recommendations
        report += "\n## Security Recommendations\n"
        report += "\n### High Priority\n"
        report += "- Conduct regular security assessments\n"
        report += "- Implement security monitoring\n"
        report += "- Keep systems and software updated\n"
        
        report += "\n### Medium Priority\n"
        report += "- Review and harden configurations\n"
        report += "- Implement security headers\n"
        report += "- Regular backup and recovery testing\n"
        
        report += "\n### Low Priority\n"
        report += "- Security awareness training\n"
        report += "- Documentation updates\n"
        report += "- Process improvements\n"
        
        report += "\n## Next Steps\n"
        report += "1. Review all findings with stakeholders\n"
        report += "2. Prioritize remediation based on risk\n"
        report += "3. Implement fixes and retest\n"
        report += "4. Schedule follow-up assessment\n"
        
        return report
    
    def _display_security_summary(self):
        """Display security assessment summary."""
        if not self.current_scan:
            return
        
        console.print("\n[bold cyan]🔒 Security Assessment Summary[/bold cyan]")
        
        # Count vulnerabilities by severity
        high_count = 0
        medium_count = 0
        low_count = 0
        info_count = 0
        
        results = self.current_scan['results']
        
        # Count from vulnerability assessment
        if 'vulnerability_assessment' in results:
            vuln = results['vulnerability_assessment']
            if 'open_ports_analysis' in vuln:
                for port_analysis in vuln['open_ports_analysis']:
                    if 'error' not in port_analysis:
                        if port_analysis['risk_level'] == 'HIGH':
                            high_count += 1
                        elif port_analysis['risk_level'] == 'MEDIUM':
                            medium_count += 1
                        elif port_analysis['risk_level'] == 'LOW':
                            low_count += 1
        
        # Count from web application testing
        if 'web_application_testing' in results:
            web = results['web_application_testing']
            for test_type, test_results in web.items():
                for result in test_results:
                    if result['severity'] == 'HIGH':
                        high_count += 1
                    elif result['severity'] == 'MEDIUM':
                        medium_count += 1
                    elif result['severity'] == 'LOW':
                        low_count += 1
                    elif result['severity'] == 'INFO':
                        info_count += 1
        
        # Display summary table
        table = Table(title="📊 Vulnerability Summary", border_style="blue")
        table.add_column("Severity", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Description", style="yellow")
        
        table.add_row("🔴 HIGH", str(high_count), "Immediate attention required")
        table.add_row("🟡 MEDIUM", str(medium_count), "Address within 30 days")
        table.add_row("🟢 LOW", str(low_count), "Address within 90 days")
        table.add_row("ℹ️ INFO", str(info_count), "Informational findings")
        
        console.print(table)
        
        # Risk assessment
        if high_count > 0:
            console.print(f"[red]🚨 CRITICAL: {high_count} high-risk vulnerabilities found![/red]")
        elif medium_count > 0:
            console.print(f"[yellow]⚠️ WARNING: {medium_count} medium-risk vulnerabilities found[/yellow]")
        else:
            console.print(f"[green]✅ Good: No high or medium-risk vulnerabilities found[/green]")
    
    def quick_scan(self, target: str):
        """Perform a quick security scan."""
        console.print(f"[cyan]⚡ Quick Security Scan: {target}[/cyan]")
        self.start_security_assessment(target, "recon")
    
    def full_scan(self, target: str):
        """Perform a full security scan."""
        console.print(f"[cyan]🔍 Full Security Scan: {target}[/cyan]")
        self.start_security_assessment(target, "full")
    
    def web_app_scan(self, target: str):
        """Perform web application security scan."""
        console.print(f"[cyan]🌐 Web Application Scan: {target}[/cyan]")
        self.start_security_assessment(target, "web")
    
    def list_reports(self):
        """List available security reports."""
        report_files = list(self.results_dir.glob("*.md"))
        
        if not report_files:
            console.print("[yellow]No security reports found.[/yellow]")
            return
        
        table = Table(title="📋 Security Reports", border_style="blue")
        table.add_column("Report", style="cyan")
        table.add_column("Target", style="green")
        table.add_column("Date", style="yellow")
        table.add_column("Size", style="magenta")
        
        for report_file in sorted(report_files, key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                # Extract target and date from filename
                parts = report_file.stem.split('_')
                if len(parts) >= 3:
                    target = parts[2]
                    date = f"{parts[3]}_{parts[4]}"
                else:
                    target = "Unknown"
                    date = "Unknown"
                
                size_kb = report_file.stat().st_size / 1024
                table.add_row(
                    report_file.name,
                    target,
                    date,
                    f"{size_kb:.1f} KB"
                )
            except Exception:
                table.add_row(report_file.name, "Error", "Error", "Error")
        
        console.print(table)
