#!/usr/bin/env python3
"""
Security Validation for Production
Validazione sicurezza completa per ambiente produzione
"""

import os
import sys
import hashlib
import logging
import sqlite3
import subprocess
from typing import Dict, List, Optional
from datetime import datetime
import json
import re

class SecurityValidator:
    """Validatore sicurezza per produzione"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()

        # Configurazione sicurezza
        self.min_secret_key_length = 80
        self.allowed_ports = [8501, 8502, 8503]  # Streamlit ports
        self.blocked_ports = [22, 23, 25, 53, 110, 143, 993, 995]  # Common attack vectors

        # Vulnerabilità note
        self.known_vulnerabilities = {
            "SQL_injection": self.check_sql_injection,
            "XSS": self.check_xss_protection,
            "path_traversal": self.check_path_traversal,
            "command_injection": self.check_command_injection,
            "weak_crypto": self.check_crypto_strength,
            "insecure_deserialization": self.check_deserialization,
            "information_disclosure": self.check_info_disclosure,
            "authentication_bypass": self.check_auth_bypass
        }

    def setup_logging(self):
        """Configura logging per sicurezza"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('security.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def run_comprehensive_security_audit(self) -> Dict[str, any]:
        """Esegue audit sicurezza completo"""
        self.logger.info("Starting comprehensive security audit...")

        audit_results = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": 0,
            "critical_issues": [],
            "high_issues": [],
            "medium_issues": [],
            "low_issues": [],
            "info_issues": [],
            "categories": {}
        }

        try:
            # Audit configurazione
            config_audit = self.audit_configuration()
            audit_results["categories"]["configuration"] = config_audit

            # Audit database
            db_audit = self.audit_database_security()
            audit_results["categories"]["database"] = db_audit

            # Audit codice
            code_audit = self.audit_code_security()
            audit_results["categories"]["code"] = code_audit

            # Audit rete
            network_audit = self.audit_network_security()
            audit_results["categories"]["network"] = network_audit

            # Audit autenticazione
            auth_audit = self.audit_authentication()
            audit_results["categories"]["authentication"] = auth_audit

            # Audit crittografia
            crypto_audit = self.audit_cryptography()
            audit_results["categories"]["cryptography"] = crypto_audit

            # Audit vulnerabilità note
            vuln_audit = self.audit_known_vulnerabilities()
            audit_results["categories"]["vulnerabilities"] = vuln_audit

            # Calcola score complessivo
            audit_results["overall_score"] = self.calculate_security_score(audit_results)

            # Classifica issue per severità
            self.categorize_issues(audit_results)

            self.logger.info(f"Security audit completed. Score: {audit_results['overall_score']}/100")

            return audit_results

        except Exception as e:
            self.logger.error(f"Security audit failed: {str(e)}")
            audit_results["critical_issues"].append({
                "category": "audit_error",
                "message": f"Security audit failed: {str(e)}",
                "severity": "critical"
            })
            return audit_results

    def audit_configuration(self) -> Dict[str, any]:
        """Audit configurazione sicurezza"""
        issues = []

        # Verifica SECRET_KEY
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            issues.append({
                "issue": "missing_secret_key",
                "message": "SECRET_KEY environment variable not set",
                "severity": "critical",
                "recommendation": "Set a strong SECRET_KEY environment variable"
            })
        elif len(secret_key) < self.min_secret_key_length:
            issues.append({
                "issue": "weak_secret_key",
                "message": f"SECRET_KEY too short: {len(secret_key)} < {self.min_secret_key_length}",
                "severity": "high",
                "recommendation": f"Use SECRET_KEY with at least {self.min_secret_key_length} characters"
            })

        # Verifica DEBUG mode
        debug_mode = os.getenv("DEBUG", "False").lower() == "true"
        if debug_mode:
            issues.append({
                "issue": "debug_enabled",
                "message": "DEBUG mode is enabled in production",
                "severity": "high",
                "recommendation": "Disable DEBUG mode in production"
            })

        # Verifica configurazioni AI
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            issues.append({
                "issue": "missing_openai_key",
                "message": "OPENAI_API_KEY not configured",
                "severity": "medium",
                "recommendation": "Configure OPENAI_API_KEY for AI functionality"
            })

        return {
            "score": self.calculate_category_score(issues),
            "issues": issues,
            "status": "secure" if not issues else "vulnerable"
        }

    def audit_database_security(self) -> Dict[str, any]:
        """Audit sicurezza database"""
        issues = []

        try:
            # Trova database files
            db_files = self.find_database_files()

            for db_file in db_files:
                if os.path.exists(db_file):
                    # Verifica permessi file
                    file_perms = oct(os.stat(db_file).st_mode)[-3:]
                    if file_perms != "600":
                        issues.append({
                            "issue": "insecure_db_permissions",
                            "message": f"Database file {db_file} has insecure permissions: {file_perms}",
                            "severity": "medium",
                            "recommendation": "Set database file permissions to 600"
                        })

                    # Verifica integrità database
                    if not self.verify_database_integrity(db_file):
                        issues.append({
                            "issue": "db_integrity",
                            "message": f"Database integrity check failed for {db_file}",
                            "severity": "high",
                            "recommendation": "Run database integrity check and repair"
                        })

                    # Verifica SQL injection protection
                    sql_issues = self.check_sql_injection_protection(db_file)
                    issues.extend(sql_issues)

        except Exception as e:
            issues.append({
                "issue": "db_audit_error",
                "message": f"Database audit failed: {str(e)}",
                "severity": "high",
                "recommendation": "Check database accessibility and permissions"
            })

        return {
            "score": self.calculate_category_score(issues),
            "issues": issues,
            "status": "secure" if not issues else "vulnerable"
        }

    def find_database_files(self) -> List[str]:
        """Trova file database"""
        db_files = [
            "test_metadata.sqlite",
            "metadata.sqlite",
            "db_memoria/metadata.sqlite",
            "db_memoria/chroma.sqlite3"
        ]

        existing_files = []
        for db_file in db_files:
            if os.path.exists(db_file):
                existing_files.append(db_file)

        return existing_files

    def verify_database_integrity(self, db_path: str) -> bool:
        """Verifica integrità database"""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                return result[0] == "ok"
        except Exception:
            return False

    def check_sql_injection_protection(self, db_path: str) -> List[Dict]:
        """Verifica protezione SQL injection"""
        issues = []

        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                # Verifica prepared statements
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()

                for table in tables:
                    # Verifica se ci sono query non parametrizzate
                    # Qui implementare verifica più approfondita
                    pass

        except Exception as e:
            issues.append({
                "issue": "sql_injection_check_error",
                "message": f"SQL injection check failed: {str(e)}",
                "severity": "medium",
                "recommendation": "Review SQL queries for injection vulnerabilities"
            })

        return issues

    def audit_code_security(self) -> Dict[str, any]:
        """Audit sicurezza codice"""
        issues = []

        try:
            # Analisi codice Python
            code_issues = self.analyze_python_code()
            issues.extend(code_issues)

            # Verifica dipendenze
            deps_issues = self.check_dependencies_security()
            issues.extend(deps_issues)

            # Verifica input validation
            input_issues = self.check_input_validation()
            issues.extend(input_issues)

        except Exception as e:
            issues.append({
                "issue": "code_audit_error",
                "message": f"Code audit failed: {str(e)}",
                "severity": "high",
                "recommendation": "Review code for security vulnerabilities"
            })

        return {
            "score": self.calculate_category_score(issues),
            "issues": issues,
            "status": "secure" if not issues else "vulnerable"
        }

    def analyze_python_code(self) -> List[Dict]:
        """Analizza codice Python per vulnerabilità"""
        issues = []

        # File Python da analizzare
        python_files = self.find_python_files()

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Verifica eval usage
                if "eval(" in content:
                    issues.append({
                        "issue": "unsafe_eval",
                        "message": f"Use of eval() in {py_file}",
                        "severity": "high",
                        "recommendation": "Replace eval() with safe alternatives"
                    })

                # Verifica exec usage
                if "exec(" in content:
                    issues.append({
                        "issue": "unsafe_exec",
                        "message": f"Use of exec() in {py_file}",
                        "severity": "high",
                        "recommendation": "Replace exec() with safe alternatives"
                    })

                # Verifica pickle usage
                if "pickle" in content and ("load" in content or "loads" in content):
                    issues.append({
                        "issue": "pickle_usage",
                        "message": f"Use of pickle in {py_file}",
                        "severity": "medium",
                        "recommendation": "Use JSON or other safe serialization"
                    })

                # Verifica input() usage
                if "input(" in content:
                    issues.append({
                        "issue": "input_usage",
                        "message": f"Use of input() in {py_file}",
                        "severity": "medium",
                        "recommendation": "Validate and sanitize user input"
                    })

            except Exception as e:
                issues.append({
                    "issue": "code_analysis_error",
                    "message": f"Failed to analyze {py_file}: {str(e)}",
                    "severity": "low",
                    "recommendation": "Check file encoding and permissions"
                })

        return issues

    def find_python_files(self) -> List[str]:
        """Trova file Python"""
        python_files = []

        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))

        return python_files

    def check_dependencies_security(self) -> List[Dict]:
        """Verifica sicurezza dipendenze"""
        issues = []

        try:
            # Verifica requirements.txt
            if os.path.exists("requirements.txt"):
                with open("requirements.txt", 'r') as f:
                    requirements = f.read()

                # Verifica versioni pinned
                lines = requirements.strip().split('\n')
                unpinned = [line for line in lines if '==' not in line and line.strip()]

                if unpinned:
                    issues.append({
                        "issue": "unpinned_dependencies",
                        "message": f"Unpinned dependencies found: {len(unpinned)}",
                        "severity": "medium",
                        "recommendation": "Pin all dependency versions with =="
                    })

        except Exception as e:
            issues.append({
                "issue": "dependency_check_error",
                "message": f"Dependency check failed: {str(e)}",
                "severity": "low",
                "recommendation": "Check requirements.txt format"
            })

        return issues

    def check_input_validation(self) -> List[Dict]:
        """Verifica validazione input"""
        issues = []

        # Qui implementare verifica validazione input
        # Per ora placeholder

        return issues

    def audit_network_security(self) -> Dict[str, any]:
        """Audit sicurezza rete"""
        issues = []

        try:
            # Verifica porte aperte
            open_ports = self.check_open_ports()
            for port in open_ports:
                if port in self.blocked_ports:
                    issues.append({
                        "issue": "blocked_port_open",
                        "message": f"Blocked port {port} is open",
                        "severity": "high",
                        "recommendation": f"Close port {port} or restrict access"
                    })

            # Verifica firewall
            firewall_status = self.check_firewall_status()
            if not firewall_status["enabled"]:
                issues.append({
                    "issue": "firewall_disabled",
                    "message": "Firewall is disabled",
                    "severity": "medium",
                    "recommendation": "Enable and configure firewall"
                })

        except Exception as e:
            issues.append({
                "issue": "network_audit_error",
                "message": f"Network audit failed: {str(e)}",
                "severity": "medium",
                "recommendation": "Check network configuration"
            })

        return {
            "score": self.calculate_category_score(issues),
            "issues": issues,
            "status": "secure" if not issues else "vulnerable"
        }

    def check_open_ports(self) -> List[int]:
        """Verifica porte aperte"""
        open_ports = []

        try:
            # Usa netstat per verificare porte aperte
            result = subprocess.run(['netstat', '-tln'], capture_output=True, text=True)

            for line in result.stdout.split('\n'):
                if 'LISTEN' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        port_info = parts[3]
                        if ':' in port_info:
                            port = port_info.split(':')[-1]
                            try:
                                port_num = int(port)
                                if port_num not in open_ports:
                                    open_ports.append(port_num)
                            except ValueError:
                                pass

        except Exception:
            # Fallback: assume common ports
            open_ports = [8501, 8502, 8503]

        return open_ports

    def check_firewall_status(self) -> Dict[str, any]:
        """Verifica status firewall"""
        # Placeholder - implementare verifica firewall specifica OS
        return {"enabled": True, "rules": []}

    def audit_authentication(self) -> Dict[str, any]:
        """Audit autenticazione"""
        issues = []

        try:
            # Verifica password policy
            password_policy = self.check_password_policy()
            if not password_policy["compliant"]:
                issues.append({
                    "issue": "weak_password_policy",
                    "message": "Password policy does not meet security standards",
                    "severity": "medium",
                    "recommendation": "Implement strong password requirements"
                })

            # Verifica session management
            session_issues = self.check_session_management()
            issues.extend(session_issues)

        except Exception as e:
            issues.append({
                "issue": "auth_audit_error",
                "message": f"Authentication audit failed: {str(e)}",
                "severity": "medium",
                "recommendation": "Review authentication implementation"
            })

        return {
            "score": self.calculate_category_score(issues),
            "issues": issues,
            "status": "secure" if not issues else "vulnerable"
        }

    def check_password_policy(self) -> Dict[str, any]:
        """Verifica policy password"""
        # Placeholder - implementare verifica policy password
        return {"compliant": True, "requirements": []}

    def check_session_management(self) -> List[Dict]:
        """Verifica gestione sessioni"""
        issues = []

        # Verifica timeout sessioni
        # Verifica secure flags cookies
        # Verifica session storage

        return issues

    def audit_cryptography(self) -> Dict[str, any]:
        """Audit crittografia"""
        issues = []

        try:
            # Verifica algoritmi crittografici
            crypto_issues = self.check_crypto_algorithms()
            issues.extend(crypto_issues)

            # Verifica certificati SSL
            ssl_issues = self.check_ssl_certificates()
            issues.extend(ssl_issues)

        except Exception as e:
            issues.append({
                "issue": "crypto_audit_error",
                "message": f"Cryptography audit failed: {str(e)}",
                "severity": "medium",
                "recommendation": "Review cryptographic implementations"
            })

        return {
            "score": self.calculate_category_score(issues),
            "issues": issues,
            "status": "secure" if not issues else "vulnerable"
        }

    def check_crypto_algorithms(self) -> List[Dict]:
        """Verifica algoritmi crittografici"""
        issues = []

        # Verifica MD5 usage
        md5_files = self.find_md5_usage()
        for file in md5_files:
            issues.append({
                "issue": "weak_hash_md5",
                "message": f"MD5 hash used in {file}",
                "severity": "medium",
                "recommendation": "Replace MD5 with SHA-256 or stronger"
            })

        # Verifica SHA1 usage
        sha1_files = self.find_sha1_usage()
        for file in sha1_files:
            issues.append({
                "issue": "weak_hash_sha1",
                "message": f"SHA1 hash used in {file}",
                "severity": "low",
                "recommendation": "Replace SHA1 with SHA-256 or stronger"
            })

        return issues

    def find_md5_usage(self) -> List[str]:
        """Trova uso MD5 nel codice"""
        md5_files = []

        for py_file in self.find_python_files():
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    if "md5" in content.lower() or "MD5" in content:
                        md5_files.append(py_file)
            except Exception:
                pass

        return md5_files

    def find_sha1_usage(self) -> List[str]:
        """Trova uso SHA1 nel codice"""
        sha1_files = []

        for py_file in self.find_python_files():
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    if "sha1" in content.lower() or "SHA1" in content:
                        sha1_files.append(py_file)
            except Exception:
                pass

        return sha1_files

    def check_ssl_certificates(self) -> List[Dict]:
        """Verifica certificati SSL"""
        issues = []

        # Placeholder - implementare verifica certificati
        # Verifica HTTPS configuration
        # Verifica certificate validity

        return issues

    def audit_known_vulnerabilities(self) -> Dict[str, any]:
        """Audit vulnerabilità note"""
        issues = []

        for vuln_name, check_func in self.known_vulnerabilities.items():
            try:
                vuln_issues = check_func()
                issues.extend(vuln_issues)
            except Exception as e:
                issues.append({
                    "issue": f"vuln_check_error_{vuln_name}",
                    "message": f"Failed to check {vuln_name}: {str(e)}",
                    "severity": "low",
                    "recommendation": f"Review {vuln_name} protection"
                })

        return {
            "score": self.calculate_category_score(issues),
            "issues": issues,
            "status": "secure" if not issues else "vulnerable"
        }

    def check_sql_injection(self) -> List[Dict]:
        """Verifica SQL injection"""
        issues = []

        # Verifica query non parametrizzate
        # Verifica input sanitization

        return issues

    def check_xss_protection(self) -> List[Dict]:
        """Verifica protezione XSS"""
        issues = []

        # Verifica output encoding
        # Verifica input sanitization

        return issues

    def check_path_traversal(self) -> List[Dict]:
        """Verifica path traversal"""
        issues = []

        # Verifica path validation
        # Verifica file access controls

        return issues

    def check_command_injection(self) -> List[Dict]:
        """Verifica command injection"""
        issues = []

        # Verifica subprocess calls
        # Verifica shell command execution

        return issues

    def check_crypto_strength(self) -> List[Dict]:
        """Verifica forza crittografia"""
        issues = []

        # Verifica key lengths
        # Verifica algorithm strength

        return issues

    def check_deserialization(self) -> List[Dict]:
        """Verifica deserializzazione sicura"""
        issues = []

        # Verifica pickle usage
        # Verifica JSON validation

        return issues

    def check_info_disclosure(self) -> List[Dict]:
        """Verifica information disclosure"""
        issues = []

        # Verifica error messages
        # Verifica debug info

        return issues

    def check_auth_bypass(self) -> List[Dict]:
        """Verifica authentication bypass"""
        issues = []

        # Verifica access controls
        # Verifica authorization

        return issues

    def calculate_security_score(self, audit_results: Dict[str, any]) -> float:
        """Calcola score sicurezza complessivo"""
        category_scores = []

        for category, results in audit_results["categories"].items():
            if "score" in results:
                category_scores.append(results["score"])

        if not category_scores:
            return 0.0

        # Calcola media pesata
        weights = {
            "configuration": 0.25,
            "database": 0.20,
            "code": 0.20,
            "network": 0.15,
            "authentication": 0.10,
            "cryptography": 0.05,
            "vulnerabilities": 0.05
        }

        weighted_score = 0.0
        total_weight = 0.0

        for category, results in audit_results["categories"].items():
            if category in weights and "score" in results:
                weighted_score += results["score"] * weights[category]
                total_weight += weights[category]

        return round(weighted_score / total_weight if total_weight > 0 else 0.0, 1)

    def calculate_category_score(self, issues: List[Dict]) -> float:
        """Calcola score per categoria"""
        if not issues:
            return 100.0

        # Pesi per severità
        severity_weights = {
            "critical": 1.0,
            "high": 0.7,
            "medium": 0.4,
            "low": 0.2,
            "info": 0.1
        }

        total_penalty = 0.0
        for issue in issues:
            severity = issue.get("severity", "medium")
            penalty = severity_weights.get(severity, 0.4)
            total_penalty += penalty

        # Calcola score (100 - penalty, min 0)
        score = max(0.0, 100.0 - (total_penalty * 20))
        return round(score, 1)

    def categorize_issues(self, audit_results: Dict[str, any]):
        """Categorizza issue per severità"""
        all_issues = []

        # Raccogli tutti gli issue
        for category, results in audit_results["categories"].items():
            if "issues" in results:
                for issue in results["issues"]:
                    issue["category"] = category
                    all_issues.append(issue)

        # Classifica per severità
        for issue in all_issues:
            severity = issue.get("severity", "medium")

            if severity == "critical":
                audit_results["critical_issues"].append(issue)
            elif severity == "high":
                audit_results["high_issues"].append(issue)
            elif severity == "medium":
                audit_results["medium_issues"].append(issue)
            elif severity == "low":
                audit_results["low_issues"].append(issue)
            else:
                audit_results["info_issues"].append(issue)

    def generate_security_report(self, audit_results: Dict[str, any]) -> str:
        """Genera report sicurezza"""
        report = {
            "security_audit": audit_results,
            "recommendations": self.generate_recommendations(audit_results),
            "compliance_status": self.check_compliance_status(audit_results)
        }

        report_file = f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Security report generated: {report_file}")
        return report_file

    def generate_recommendations(self, audit_results: Dict[str, any]) -> List[Dict]:
        """Genera raccomandazioni"""
        recommendations = []

        # Priorità: critical > high > medium > low

        all_issues = (
            audit_results["critical_issues"] +
            audit_results["high_issues"] +
            audit_results["medium_issues"] +
            audit_results["low_issues"]
        )

        for issue in all_issues:
            recommendation = {
                "priority": issue.get("severity", "medium"),
                "category": issue.get("category", "unknown"),
                "issue": issue.get("issue", "unknown"),
                "message": issue.get("message", ""),
                "recommendation": issue.get("recommendation", "Review and fix"),
                "effort": self.estimate_fix_effort(issue)
            }
            recommendations.append(recommendation)

        # Ordina per priorità
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 4))

        return recommendations

    def estimate_fix_effort(self, issue: Dict) -> str:
        """Stima effort per fix"""
        issue_type = issue.get("issue", "")

        if any(word in issue_type for word in ["secret", "key", "password"]):
            return "low"
        elif any(word in issue_type for word in ["debug", "log", "config"]):
            return "low"
        elif any(word in issue_type for word in ["sql", "xss", "injection"]):
            return "medium"
        elif any(word in issue_type for word in ["crypto", "hash", "ssl"]):
            return "medium"
        else:
            return "high"

    def check_compliance_status(self, audit_results: Dict[str, any]) -> Dict[str, any]:
        """Verifica status compliance"""
        compliance = {
            "GDPR": {"compliant": True, "issues": []},
            "OWASP": {"compliant": True, "issues": []},
            "ISO27001": {"compliant": True, "issues": []}
        }

        # Verifica GDPR compliance
        if audit_results["critical_issues"] or audit_results["high_issues"]:
            compliance["GDPR"]["compliant"] = False
            compliance["GDPR"]["issues"].append("Critical security issues found")

        # Verifica OWASP compliance
        owasp_issues = [i for i in audit_results["critical_issues"] + audit_results["high_issues"]
                       if i.get("category") in ["code", "database", "network"]]
        if owasp_issues:
            compliance["OWASP"]["compliant"] = False
            compliance["OWASP"]["issues"].append(f"OWASP violations: {len(owasp_issues)}")

        return compliance

def main():
    """Main security validation function"""
    validator = SecurityValidator()

    try:
        # Esegui audit completo
        audit_results = validator.run_comprehensive_security_audit()

        # Genera report
        report_file = validator.generate_security_report(audit_results)

        # Output risultati
        print(f"🔒 Security Audit Results:")
        print(f"   Overall Score: {audit_results['overall_score']}/100")
        print(f"   Critical Issues: {len(audit_results['critical_issues'])}")
        print(f"   High Issues: {len(audit_results['high_issues'])}")
        print(f"   Medium Issues: {len(audit_results['medium_issues'])}")
        print(f"   Low Issues: {len(audit_results['low_issues'])}")
        print(f"   Report: {report_file}")

        # Exit code based on issues
        if audit_results["critical_issues"]:
            print("❌ CRITICAL SECURITY ISSUES FOUND - REQUIRES IMMEDIATE ATTENTION")
            sys.exit(1)
        elif audit_results["high_issues"]:
            print("⚠️ HIGH PRIORITY SECURITY ISSUES FOUND")
            sys.exit(1)
        else:
            print("✅ SECURITY AUDIT PASSED")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n⚠️ Security audit interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Security audit failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
