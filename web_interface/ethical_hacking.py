#!/usr/bin/env python3
"""
🔒 Enhanced Ethical Hacking & Network Security Module
Advanced vulnerability scanning, network reconnaissance, and security assessment tools
"""

import os
import sys
import json
import time
import socket
import subprocess
import threading
import asyncio
import nmap
import requests
import dns.resolver
import whois
import ssl
import OpenSSL
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress
import hashlib
import base64
import re

class NetworkScanner:
    """Advanced network scanning and reconnaissance"""
    
    def __init__(self):
        self.scan_results = {}
        self.active_scans = {}
        self.scan_history = []
        
    def scan_network_range(self, network_range: str, scan_type: str = 'comprehensive') -> Dict[str, Any]:
        """Scan entire network range for live hosts and services"""
        try:
            scan_id = f"scan_{int(time.time())}"
            self.active_scans[scan_id] = {'status': 'running', 'progress': 0}
            
            # Parse network range
            network = ipaddress.ip_network(network_range, strict=False)
            total_hosts = network.num_addresses
            
            results = {
                'scan_id': scan_id,
                'network': str(network),
                'total_hosts': total_hosts,
                'live_hosts': [],
                'services': {},
                'vulnerabilities': [],
                'scan_type': scan_type,
                'start_time': datetime.now().isoformat()
            }
            
            # Use nmap for network discovery
            nm = nmap.PortScanner()
            
            if scan_type == 'quick':
                nm.scan(hosts=str(network), arguments='-sn -T4')
            elif scan_type == 'comprehensive':
                nm.scan(hosts=str(network), arguments='-sS -sV -O -A -T4 --script=vuln')
            else:  # stealth
                nm.scan(hosts=str(network), arguments='-sS -sV -T2 --script=vuln')
            
            # Process results
            for host in nm.all_hosts():
                if nm[host].state() == 'up':
                    host_info = {
                        'ip': host,
                        'hostname': nm[host].hostname() or 'Unknown',
                        'os': nm[host].get('osmatch', [{}])[0].get('name', 'Unknown') if 'osmatch' in nm[host] else 'Unknown',
                        'ports': [],
                        'services': [],
                        'vulnerabilities': []
                    }
                    
                    # Get open ports and services
                    for proto in nm[host].all_protocols():
                        ports = nm[host][proto].keys()
                        for port in ports:
                            service_info = nm[host][proto][port]
                            port_info = {
                                'port': port,
                                'protocol': proto,
                                'service': service_info.get('name', 'unknown'),
                                'version': service_info.get('version', ''),
                                'state': service_info.get('state', 'open')
                            }
                            host_info['ports'].append(port_info)
                            host_info['services'].append(f"{port_info['service']}:{port}")
                    
                    # Check for common vulnerabilities
                    if 'script' in nm[host]:
                        for script_name, script_output in nm[host]['script'].items():
                            if 'vuln' in script_name.lower():
                                host_info['vulnerabilities'].append({
                                    'script': script_name,
                                    'output': script_output
                                })
                    
                    results['live_hosts'].append(host_info)
                    self.active_scans[scan_id]['progress'] = len(results['live_hosts']) / total_hosts * 100
            
            results['end_time'] = datetime.now().isoformat()
            results['duration'] = (datetime.fromisoformat(results['end_time']) - 
                                 datetime.fromisoformat(results['start_time'])).total_seconds()
            
            self.scan_results[scan_id] = results
            self.scan_history.append(results)
            self.active_scans[scan_id]['status'] = 'completed'
            
            return results
            
        except Exception as e:
            if scan_id in self.active_scans:
                self.active_scans[scan_id]['status'] = 'failed'
                self.active_scans[scan_id]['error'] = str(e)
            return {'error': str(e)}

class VulnerabilityScanner:
    """Advanced vulnerability assessment and exploitation testing"""
    
    def __init__(self):
        self.vuln_database = self._load_vulnerability_database()
        self.scan_results = {}
        
    def _load_vulnerability_database(self) -> Dict[str, Any]:
        """Load comprehensive vulnerability database"""
        return {
            'web_vulnerabilities': {
                'sql_injection': {
                    'description': 'SQL injection vulnerability',
                    'severity': 'High',
                    'payloads': ["' OR '1'='1", "'; DROP TABLE users; --", "1' UNION SELECT 1,2,3--"],
                    'detection': 'Check for SQL errors in responses'
                },
                'xss': {
                    'description': 'Cross-site scripting vulnerability',
                    'severity': 'High',
                    'payloads': ['<script>alert("XSS")</script>', 'javascript:alert("XSS")'],
                    'detection': 'Check for script execution in responses'
                },
                'csrf': {
                    'description': 'Cross-site request forgery',
                    'severity': 'Medium',
                    'detection': 'Check for missing CSRF tokens'
                }
            },
            'network_vulnerabilities': {
                'open_ports': {
                    'description': 'Unnecessary open ports',
                    'severity': 'Medium',
                    'detection': 'Port scanning'
                },
                'weak_ssl': {
                    'description': 'Weak SSL/TLS configuration',
                    'severity': 'High',
                    'detection': 'SSL/TLS testing'
                }
            }
        }
    
    def scan_target(self, target: str, scan_type: str = 'comprehensive') -> Dict[str, Any]:
        """Comprehensive vulnerability scan of a target"""
        try:
            scan_id = f"vuln_scan_{int(time.time())}"
            
            results = {
                'scan_id': scan_id,
                'target': target,
                'scan_type': scan_type,
                'start_time': datetime.now().isoformat(),
                'vulnerabilities': [],
                'services': {},
                'risk_score': 0,
                'recommendations': []
            }
            
            # Port and service discovery
            open_ports = self._discover_ports(target)
            results['services'] = open_ports
            
            # Web application testing
            if any(port in [80, 443, 8080, 8443] for port in open_ports.keys()):
                web_vulns = self._test_web_vulnerabilities(target, open_ports)
                results['vulnerabilities'].extend(web_vulns)
            
            # SSL/TLS testing
            if 443 in open_ports or 8443 in open_ports:
                ssl_vulns = self._test_ssl_vulnerabilities(target)
                results['vulnerabilities'].extend(ssl_vulns)
            
            # Network service testing
            network_vulns = self._test_network_services(target, open_ports)
            results['vulnerabilities'].extend(network_vulns)
            
            # Calculate risk score
            results['risk_score'] = self._calculate_risk_score(results['vulnerabilities'])
            
            # Generate recommendations
            results['recommendations'] = self._generate_recommendations(results['vulnerabilities'])
            
            results['end_time'] = datetime.now().isoformat()
            results['duration'] = (datetime.fromisoformat(results['end_time']) - 
                                 datetime.fromisoformat(results['start_time'])).total_seconds()
            
            self.scan_results[scan_id] = results
            return results
            
        except Exception as e:
            return {'error': str(e)}
    
    def _discover_ports(self, target: str) -> Dict[int, str]:
        """Discover open ports and services"""
        try:
            common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 8080, 8443, 3306, 5432, 6379, 27017]
            open_ports = {}
            
            for port in common_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((target, port))
                    if result == 0:
                        # Try to identify service
                        service = self._identify_service(target, port)
                        open_ports[port] = service
                    sock.close()
                except:
                    continue
            
            return open_ports
        except Exception as e:
            return {}
    
    def _identify_service(self, target: str, port: int) -> str:
        """Identify service running on port"""
        try:
            service_names = {
                21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS',
                80: 'HTTP', 110: 'POP3', 143: 'IMAP', 443: 'HTTPS',
                993: 'IMAPS', 995: 'POP3S', 8080: 'HTTP-Alt', 8443: 'HTTPS-Alt',
                3306: 'MySQL', 5432: 'PostgreSQL', 6379: 'Redis', 27017: 'MongoDB'
            }
            return service_names.get(port, 'Unknown')
        except:
            return 'Unknown'
    
    def _test_web_vulnerabilities(self, target: str, open_ports: Dict[int, str]) -> List[Dict[str, Any]]:
        """Test for common web vulnerabilities"""
        vulnerabilities = []
        
        try:
            # Determine protocol and port
            if 443 in open_ports or 8443 in open_ports:
                protocol = 'https'
                port = 443 if 443 in open_ports else 8443
            else:
                protocol = 'http'
                port = 80 if 80 in open_ports else 8080
            
            base_url = f"{protocol}://{target}:{port}"
            
            # Test for common vulnerabilities
            vulns = self._test_sql_injection(base_url)
            vulnerabilities.extend(vulns)
            
            vulns = self._test_xss(base_url)
            vulnerabilities.extend(vulns)
            
            vulns = self._test_directory_traversal(base_url)
            vulnerabilities.extend(vulns)
            
        except Exception as e:
            vulnerabilities.append({
                'type': 'error',
                'description': f'Error testing web vulnerabilities: {str(e)}',
                'severity': 'Info'
            })
        
        return vulnerabilities
    
    def _test_sql_injection(self, base_url: str) -> List[Dict[str, Any]]:
        """Test for SQL injection vulnerabilities"""
        vulnerabilities = []
        test_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1' UNION SELECT 1,2,3--",
            "admin'--",
            "1' AND 1=1--"
        ]
        
        try:
            for payload in test_payloads:
                test_url = f"{base_url}/?id={payload}"
                try:
                    response = requests.get(test_url, timeout=5)
                    if any(error in response.text.lower() for error in ['sql', 'mysql', 'postgresql', 'oracle', 'sqlite']):
                        vulnerabilities.append({
                            'type': 'sql_injection',
                            'description': f'Potential SQL injection with payload: {payload}',
                            'severity': 'High',
                            'payload': payload,
                            'url': test_url,
                            'response_code': response.status_code
                        })
                except:
                    continue
        except Exception as e:
            vulnerabilities.append({
                'type': 'error',
                'description': f'Error testing SQL injection: {str(e)}',
                'severity': 'Info'
            })
        
        return vulnerabilities
    
    def _test_xss(self, base_url: str) -> List[Dict[str, Any]]:
        """Test for XSS vulnerabilities"""
        vulnerabilities = []
        test_payloads = [
            '<script>alert("XSS")</script>',
            'javascript:alert("XSS")',
            '<img src=x onerror=alert("XSS")>',
            '"><script>alert("XSS")</script>'
        ]
        
        try:
            for payload in test_payloads:
                test_url = f"{base_url}/?search={payload}"
                try:
                    response = requests.get(test_url, timeout=5)
                    if payload in response.text:
                        vulnerabilities.append({
                            'type': 'xss',
                            'description': f'Potential XSS vulnerability with payload: {payload}',
                            'severity': 'High',
                            'payload': payload,
                            'url': test_url,
                            'response_code': response.status_code
                        })
                except:
                    continue
        except Exception as e:
            vulnerabilities.append({
                'type': 'error',
                'description': f'Error testing XSS: {str(e)}',
                'severity': 'Info'
            })
        
        return vulnerabilities
    
    def _test_directory_traversal(self, base_url: str) -> List[Dict[str, Any]]:
        """Test for directory traversal vulnerabilities"""
        vulnerabilities = []
        test_payloads = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
            '....//....//....//etc/passwd',
            '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd'
        ]
        
        try:
            for payload in test_payloads:
                test_url = f"{base_url}/?file={payload}"
                try:
                    response = requests.get(test_url, timeout=5)
                    if any(indicator in response.text.lower() for indicator in ['root:', 'bin:', 'daemon:', 'adm:']):
                        vulnerabilities.append({
                            'type': 'directory_traversal',
                            'description': f'Potential directory traversal with payload: {payload}',
                            'severity': 'High',
                            'payload': payload,
                            'url': test_url,
                            'response_code': response.status_code
                        })
                except:
                    continue
        except Exception as e:
            vulnerabilities.append({
                'type': 'error',
                'description': f'Error testing directory traversal: {str(e)}',
                'severity': 'Info'
            })
        
        return vulnerabilities
    
    def _test_ssl_vulnerabilities(self, target: str) -> List[Dict[str, Any]]:
        """Test SSL/TLS configuration for vulnerabilities"""
        vulnerabilities = []
        
        try:
            context = ssl.create_default_context()
            with socket.create_connection((target, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=target) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    
                    # Check certificate validity
                    if not cert:
                        vulnerabilities.append({
                            'type': 'ssl_certificate',
                            'description': 'No SSL certificate found',
                            'severity': 'High'
                        })
                    else:
                        # Check expiration
                        not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                        if not_after < datetime.now():
                            vulnerabilities.append({
                                'type': 'ssl_certificate',
                                'description': 'SSL certificate has expired',
                                'severity': 'High',
                                'expiry_date': not_after.isoformat()
                            })
                        
                        # Check weak ciphers
                        weak_ciphers = ['RC4', 'DES', '3DES', 'MD5']
                        if any(weak in str(cipher) for weak in weak_ciphers):
                            vulnerabilities.append({
                                'type': 'ssl_cipher',
                                'description': f'Weak SSL cipher detected: {cipher[0]}',
                                'severity': 'Medium',
                                'cipher': cipher[0]
                            })
        
        except Exception as e:
            vulnerabilities.append({
                'type': 'ssl_error',
                'description': f'Error testing SSL: {str(e)}',
                'severity': 'Info'
            })
        
        return vulnerabilities
    
    def _test_network_services(self, target: str, open_ports: Dict[int, str]) -> List[Dict[str, Any]]:
        """Test network services for vulnerabilities"""
        vulnerabilities = []
        
        try:
            # Test SSH
            if 22 in open_ports:
                ssh_vulns = self._test_ssh_vulnerabilities(target)
                vulnerabilities.extend(ssh_vulns)
            
            # Test FTP
            if 21 in open_ports:
                ftp_vulns = self._test_ftp_vulnerabilities(target)
                vulnerabilities.extend(ftp_vulns)
            
            # Test DNS
            if 53 in open_ports:
                dns_vulns = self._test_dns_vulnerabilities(target)
                vulnerabilities.extend(dns_vulns)
        
        except Exception as e:
            vulnerabilities.append({
                'type': 'error',
                'description': f'Error testing network services: {str(e)}',
                'severity': 'Info'
            })
        
        return vulnerabilities
    
    def _test_ssh_vulnerabilities(self, target: str) -> List[Dict[str, Any]]:
        """Test SSH service for vulnerabilities"""
        vulnerabilities = []
        
        try:
            # Test for SSH version disclosure
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((target, 22))
            
            # Receive banner
            banner = sock.recv(1024).decode('utf-8', errors='ignore')
            sock.close()
            
            if banner:
                # Check for old SSH versions
                if 'SSH-1.99' in banner or 'SSH-1.5' in banner:
                    vulnerabilities.append({
                        'type': 'ssh_version',
                        'description': 'Old SSH version detected',
                        'severity': 'Medium',
                        'banner': banner.strip()
                    })
                
                # Check for specific vulnerable versions
                vulnerable_versions = ['OpenSSH_4.3', 'OpenSSH_4.4', 'OpenSSH_4.5']
                for version in vulnerable_versions:
                    if version in banner:
                        vulnerabilities.append({
                            'type': 'ssh_vulnerable_version',
                            'description': f'Potentially vulnerable SSH version: {version}',
                            'severity': 'High',
                            'banner': banner.strip()
                        })
        
        except Exception as e:
            vulnerabilities.append({
                'type': 'ssh_error',
                'description': f'Error testing SSH: {str(e)}',
                'severity': 'Info'
            })
        
        return vulnerabilities
    
    def _test_ftp_vulnerabilities(self, target: str) -> List[Dict[str, Any]]:
        """Test FTP service for vulnerabilities"""
        vulnerabilities = []
        
        try:
            # Test for anonymous access
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((target, 21))
            
            # Receive banner
            banner = sock.recv(1024).decode('utf-8', errors='ignore')
            sock.close()
            
            if banner:
                # Check for anonymous access
                if 'anonymous' in banner.lower():
                    vulnerabilities.append({
                        'type': 'ftp_anonymous',
                        'description': 'FTP anonymous access enabled',
                        'severity': 'Medium',
                        'banner': banner.strip()
                    })
                
                # Check for old FTP versions
                if 'vsftpd 2.3.4' in banner:
                    vulnerabilities.append({
                        'type': 'ftp_vulnerable_version',
                        'description': 'Potentially vulnerable FTP version: vsftpd 2.3.4',
                        'severity': 'High',
                        'banner': banner.strip()
                    })
        
        except Exception as e:
            vulnerabilities.append({
                'type': 'ftp_error',
                'description': f'Error testing FTP: {str(e)}',
                'severity': 'Info'
            })
        
        return vulnerabilities
    
    def _test_dns_vulnerabilities(self, target: str) -> List[Dict[str, Any]]:
        """Test DNS service for vulnerabilities"""
        vulnerabilities = []
        
        try:
            # Test for DNS zone transfer
            try:
                answers = dns.resolver.resolve(target, 'NS')
                for answer in answers:
                    try:
                        zone_transfer = dns.query.xfr(str(answer), target)
                        if zone_transfer:
                            vulnerabilities.append({
                                'type': 'dns_zone_transfer',
                                'description': f'DNS zone transfer allowed from {answer}',
                                'severity': 'High',
                                'nameserver': str(answer)
                            })
                    except:
                        continue
            except:
                pass
            
            # Test for DNS recursion
            try:
                resolver = dns.resolver.Resolver()
                resolver.nameservers = [target]
                resolver.query('google.com', 'A')
                vulnerabilities.append({
                    'type': 'dns_recursion',
                    'description': 'DNS recursion enabled (potential DDoS amplification)',
                    'severity': 'Medium'
                })
            except:
                pass
        
        except Exception as e:
            vulnerabilities.append({
                'type': 'dns_error',
                'description': f'Error testing DNS: {str(e)}',
                'severity': 'Info'
            })
        
        return vulnerabilities
    
    def _calculate_risk_score(self, vulnerabilities: List[Dict[str, Any]]) -> int:
        """Calculate overall risk score based on vulnerabilities"""
        score = 0
        severity_weights = {'Low': 1, 'Medium': 3, 'High': 5, 'Critical': 10}
        
        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'Low')
            score += severity_weights.get(severity, 1)
        
        # Normalize to 0-100 scale
        return min(score * 2, 100)
    
    def _generate_recommendations(self, vulnerabilities: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable security recommendations"""
        recommendations = []
        
        for vuln in vulnerabilities:
            vuln_type = vuln.get('type', '')
            
            if 'sql_injection' in vuln_type:
                recommendations.append('Implement input validation and parameterized queries')
            elif 'xss' in vuln_type:
                recommendations.append('Implement output encoding and Content Security Policy')
            elif 'directory_traversal' in vuln_type:
                recommendations.append('Validate and sanitize file path inputs')
            elif 'ssl' in vuln_type:
                recommendations.append('Update SSL/TLS configuration and renew certificates')
            elif 'ssh' in vuln_type:
                recommendations.append('Update SSH to latest version and disable weak algorithms')
            elif 'ftp' in vuln_type:
                recommendations.append('Disable anonymous access and update FTP server')
            elif 'dns' in vuln_type:
                recommendations.append('Configure DNS security and disable unnecessary features')
        
        # Add general recommendations
        if vulnerabilities:
            recommendations.extend([
                'Implement regular security updates and patches',
                'Use security headers and HTTPS everywhere',
                'Implement proper access controls and authentication',
                'Regular security audits and penetration testing'
            ])
        
        return list(set(recommendations))  # Remove duplicates

class SocialEngineering:
    """Advanced social engineering and reconnaissance techniques"""
    
    def __init__(self):
        self.reconnaissance_data = {}
        
    def gather_target_information(self, target: str) -> Dict[str, Any]:
        """Gather comprehensive information about a target"""
        try:
            results = {
                'target': target,
                'timestamp': datetime.now().isoformat(),
                'dns_info': {},
                'whois_info': {},
                'subdomains': [],
                'email_addresses': [],
                'social_media': {},
                'technologies': [],
                'employees': [],
                'infrastructure': {}
            }
            
            # DNS reconnaissance
            results['dns_info'] = self._dns_reconnaissance(target)
            
            # WHOIS information
            results['whois_info'] = self._whois_lookup(target)
            
            # Subdomain enumeration
            results['subdomains'] = self._enumerate_subdomains(target)
            
            # Technology detection
            results['technologies'] = self._detect_technologies(target)
            
            # Infrastructure mapping
            results['infrastructure'] = self._map_infrastructure(target)
            
            return results
            
        except Exception as e:
            return {'error': str(e)}
    
    def _dns_reconnaissance(self, target: str) -> Dict[str, Any]:
        """Perform comprehensive DNS reconnaissance"""
        try:
            dns_info = {}
            
            # Common record types
            record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME']
            
            for record_type in record_types:
                try:
                    answers = dns.resolver.resolve(target, record_type)
                    dns_info[record_type] = [str(answer) for answer in answers]
                except:
                    dns_info[record_type] = []
            
            # Reverse DNS lookup
            try:
                ip = socket.gethostbyname(target)
                reverse_dns = socket.gethostbyaddr(ip)
                dns_info['reverse_dns'] = reverse_dns[0]
                dns_info['ip_address'] = ip
            except:
                dns_info['reverse_dns'] = None
                dns_info['ip_address'] = None
            
            return dns_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _whois_lookup(self, target: str) -> Dict[str, Any]:
        """Perform WHOIS lookup for domain information"""
        try:
            whois_info = whois.whois(target)
            return {
                'registrar': whois_info.registrar,
                'creation_date': str(whois_info.creation_date),
                'expiration_date': str(whois_info.expiration_date),
                'updated_date': str(whois_info.updated_date),
                'name_servers': whois_info.name_servers,
                'status': whois_info.status,
                'emails': whois_info.emails
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _enumerate_subdomains(self, target: str) -> List[str]:
        """Enumerate subdomains using various techniques"""
        subdomains = []
        
        try:
            # Common subdomain wordlist
            common_subdomains = [
                'www', 'mail', 'ftp', 'admin', 'blog', 'dev', 'test', 'staging',
                'api', 'cdn', 'support', 'help', 'docs', 'wiki', 'forum',
                'shop', 'store', 'app', 'mobile', 'web', 'secure', 'portal'
            ]
            
            for subdomain in common_subdomains:
                full_domain = f"{subdomain}.{target}"
                try:
                    ip = socket.gethostbyname(full_domain)
                    subdomains.append({
                        'subdomain': full_domain,
                        'ip': ip,
                        'status': 'active'
                    })
                except:
                    continue
            
            # DNS bruteforce with common words
            dns_words = ['ns1', 'ns2', 'mx1', 'mx2', 'smtp', 'pop', 'imap']
            for word in dns_words:
                full_domain = f"{word}.{target}"
                try:
                    ip = socket.gethostbyname(full_domain)
                    subdomains.append({
                        'subdomain': full_domain,
                        'ip': ip,
                        'status': 'active'
                    })
                except:
                    continue
                    
        except Exception as e:
            pass
        
        return subdomains
    
    def _detect_technologies(self, target: str) -> List[str]:
        """Detect technologies used by the target"""
        technologies = []
        
        try:
            # Test for common web technologies
            test_urls = [
                f"http://{target}",
                f"https://{target}",
                f"http://{target}:8080",
                f"https://{target}:8443"
            ]
            
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=5, allow_redirects=True)
                    
                    # Check headers for technology indicators
                    headers = response.headers
                    
                    if 'Server' in headers:
                        technologies.append(f"Server: {headers['Server']}")
                    
                    if 'X-Powered-By' in headers:
                        technologies.append(f"Powered by: {headers['X-Powered-By']}")
                    
                    if 'X-AspNet-Version' in headers:
                        technologies.append(f"ASP.NET: {headers['X-AspNet-Version']}")
                    
                    if 'X-PHP-Version' in headers:
                        technologies.append(f"PHP: {headers['X-PHP-Version']}")
                    
                    # Check response content for technology indicators
                    content = response.text.lower()
                    
                    if 'wordpress' in content:
                        technologies.append('WordPress')
                    elif 'drupal' in content:
                        technologies.append('Drupal')
                    elif 'joomla' in content:
                        technologies.append('Joomla')
                    elif 'laravel' in content:
                        technologies.append('Laravel')
                    elif 'django' in content:
                        technologies.append('Django')
                    elif 'flask' in content:
                        technologies.append('Flask')
                    elif 'react' in content:
                        technologies.append('React')
                    elif 'angular' in content:
                        technologies.append('Angular')
                    elif 'vue' in content:
                        technologies.append('Vue.js')
                    
                except:
                    continue
                    
        except Exception as e:
            pass
        
        return list(set(technologies))  # Remove duplicates
    
    def _map_infrastructure(self, target: str) -> Dict[str, Any]:
        """Map target infrastructure and services"""
        infrastructure = {}
        
        try:
            # Common ports to check
            common_ports = {
                21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS',
                80: 'HTTP', 110: 'POP3', 143: 'IMAP', 443: 'HTTPS',
                993: 'IMAPS', 995: 'POP3S', 8080: 'HTTP-Alt', 8443: 'HTTPS-Alt',
                3306: 'MySQL', 5432: 'PostgreSQL', 6379: 'Redis', 27017: 'MongoDB'
            }
            
            open_services = {}
            
            for port, service_name in common_ports.items():
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((target, port))
                    if result == 0:
                        open_services[port] = service_name
                    sock.close()
                except:
                    continue
            
            infrastructure['open_services'] = open_services
            infrastructure['total_services'] = len(open_services)
            
            # Check for load balancers
            try:
                response1 = requests.get(f"http://{target}", timeout=5)
                response2 = requests.get(f"http://{target}", timeout=5)
                
                if response1.headers.get('Server') != response2.headers.get('Server'):
                    infrastructure['load_balancer'] = 'Detected'
                else:
                    infrastructure['load_balancer'] = 'Not detected'
            except:
                infrastructure['load_balancer'] = 'Unknown'
            
        except Exception as e:
            infrastructure['error'] = str(e)
        
        return infrastructure

# Initialize ethical hacking components
network_scanner = NetworkScanner()
vulnerability_scanner = VulnerabilityScanner()
social_engineering = SocialEngineering()

def get_ethical_hacking_tools():
    """Get available ethical hacking tools"""
    return {
        'network_scanner': network_scanner,
        'vulnerability_scanner': vulnerability_scanner,
        'social_engineering': social_engineering
    }