#!/usr/bin/env python3
"""Comprehensive security audit script for production deployment."""

import sys
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime


class SecurityAuditor:
    """Comprehensive security audit for the code execution platform."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "audit_version": "1.0.0",
            "findings": [],
            "recommendations": [],
            "production_ready": False,
            "risk_level": "HIGH",
        }

    def run_full_audit(self):
        """Run complete security audit."""
        print("🔒 COMPREHENSIVE SECURITY AUDIT")
        print("=" * 60)
        print(f"Project: Code Execution Platform")
        print(f"Timestamp: {self.audit_results['timestamp']}")
        print(f"Audit Version: {self.audit_results['audit_version']}")
        print()

        # Run all audit checks
        self._audit_code_validation()
        self._audit_environment_security()
        self._audit_docker_security()
        self._audit_api_security()
        self._audit_dependency_security()
        self._audit_configuration_security()
        
        # Generate final report
        self._generate_audit_report()
        self._save_audit_results()

    def _audit_code_validation(self):
        """Audit code validation mechanisms."""
        print("🔍 AUDITING CODE VALIDATION")
        print("-" * 30)
        
        findings = []
        
        # Check CodeValidator implementation
        validator_file = self.project_root / "backend" / "app" / "services" / "code_validator.py"
        if validator_file.exists():
            with open(validator_file) as f:
                content = f.read()
                
                # Check for comment sanitization vulnerability
                if 'if \'#\' in line and not (\'"\'in line or "\'" in line):' in content:
                    findings.append({
                        "severity": "CRITICAL",
                        "category": "Code Validation",
                        "issue": "Comment sanitization vulnerability",
                        "description": "Comment removal logic can be bypassed when quotes are present in the line",
                        "file": str(validator_file),
                        "recommendation": "Implement proper Python tokenization for comment removal"
                    })
                
                # Check for seccomp configuration
                if 'seccomp=unconfined' in content:
                    findings.append({
                        "severity": "HIGH",
                        "category": "Container Security", 
                        "issue": "Seccomp disabled",
                        "description": "Docker seccomp profile is disabled, reducing container security",
                        "file": str(validator_file),
                        "recommendation": "Enable restrictive seccomp profile"
                    })
        
        self.audit_results["findings"].extend(findings)
        
        for finding in findings:
            print(f"   {finding['severity']}: {finding['issue']}")
        
        if not findings:
            print("   ✅ No critical validation issues found")

    def _audit_environment_security(self):
        """Audit environment and credential security."""
        print("\n🔐 AUDITING ENVIRONMENT SECURITY")
        print("-" * 30)
        
        findings = []
        
        # Check for .env files with credentials
        env_files = list(self.project_root.rglob("*.env"))
        for env_file in env_files:
            if env_file.name != ".env.example":
                try:
                    with open(env_file) as f:
                        content = f.read()
                        
                        # Check for hardcoded AWS credentials
                        if "AKIA" in content:
                            findings.append({
                                "severity": "CRITICAL",
                                "category": "Credential Security",
                                "issue": "Hardcoded AWS credentials",
                                "description": f"AWS credentials found in {env_file}",
                                "file": str(env_file),
                                "recommendation": "Remove hardcoded credentials, use environment variables"
                            })
                except Exception:
                    pass
        
        # Check .gitignore for .env exclusion
        gitignore_file = self.project_root / ".gitignore"
        if gitignore_file.exists():
            with open(gitignore_file) as f:
                gitignore_content = f.read()
                if ".env" not in gitignore_content:
                    findings.append({
                        "severity": "HIGH",
                        "category": "Credential Security",
                        "issue": ".env files not gitignored",
                        "description": "Environment files may be committed to repository",
                        "file": str(gitignore_file),
                        "recommendation": "Add .env to .gitignore"
                    })
        
        self.audit_results["findings"].extend(findings)
        
        for finding in findings:
            print(f"   {finding['severity']}: {finding['issue']}")
        
        if not findings:
            print("   ✅ No environment security issues found")

    def _audit_docker_security(self):
        """Audit Docker security configuration."""
        print("\n🐳 AUDITING DOCKER SECURITY")
        print("-" * 30)
        
        findings = []
        
        # Check Dockerfile.execution
        docker_file = self.project_root / "docker" / "Dockerfile.execution"
        if docker_file.exists():
            with open(docker_file) as f:
                content = f.read()
                
                # Check for non-root user
                if "USER coderunner" not in content:
                    findings.append({
                        "severity": "HIGH",
                        "category": "Container Security",
                        "issue": "Missing non-root user",
                        "description": "Container may run as root user",
                        "file": str(docker_file),
                        "recommendation": "Add non-root user configuration"
                    })
                
                # Check for security hardening
                security_measures = [
                    "useradd -r",  # System user
                    "apt-get remove",  # Remove dangerous tools
                    "rm -rf /var/lib/apt/lists/*",  # Clean package cache
                ]
                
                for measure in security_measures:
                    if measure not in content:
                        findings.append({
                            "severity": "MEDIUM",
                            "category": "Container Security",
                            "issue": f"Missing security measure: {measure}",
                            "description": "Container hardening could be improved",
                            "file": str(docker_file),
                            "recommendation": f"Add {measure} to Dockerfile"
                        })
        
        self.audit_results["findings"].extend(findings)
        
        for finding in findings:
            print(f"   {finding['severity']}: {finding['issue']}")
        
        if not findings:
            print("   ✅ No Docker security issues found")

    def _audit_api_security(self):
        """Audit API security configuration."""
        print("\n🌐 AUDITING API SECURITY")
        print("-" * 30)
        
        findings = []
        
        # Check for rate limiting
        api_file = self.project_root / "backend" / "app" / "api" / "v1" / "endpoints" / "code_execution.py"
        if api_file.exists():
            with open(api_file) as f:
                content = f.read()
                
                if "@limiter.limit" not in content:
                    findings.append({
                        "severity": "HIGH",
                        "category": "API Security",
                        "issue": "Missing rate limiting",
                        "description": "API endpoints lack rate limiting protection",
                        "file": str(api_file),
                        "recommendation": "Implement rate limiting on all endpoints"
                    })
                
                if "HTTPException" not in content:
                    findings.append({
                        "severity": "MEDIUM",
                        "category": "API Security",
                        "issue": "Insufficient error handling",
                        "description": "API may not handle errors securely",
                        "file": str(api_file),
                        "recommendation": "Implement comprehensive error handling"
                    })
        
        self.audit_results["findings"].extend(findings)
        
        for finding in findings:
            print(f"   {finding['severity']}: {finding['issue']}")
        
        if not findings:
            print("   ✅ No API security issues found")

    def _audit_dependency_security(self):
        """Audit dependency security."""
        print("\n📦 AUDITING DEPENDENCY SECURITY")
        print("-" * 30)
        
        findings = []
        
        # Check for known vulnerable packages (simplified check)
        pyproject_file = self.project_root / "backend" / "pyproject.toml"
        if pyproject_file.exists():
            with open(pyproject_file) as f:
                content = f.read()
                
                # Check for potentially vulnerable dependencies
                vulnerable_patterns = [
                    "requests <",  # Old requests versions
                    "urllib3 <",  # Old urllib3 versions
                    "sqlalchemy <2",  # Old SQLAlchemy versions
                ]
                
                for pattern in vulnerable_patterns:
                    if pattern in content:
                        findings.append({
                            "severity": "MEDIUM",
                            "category": "Dependency Security",
                            "issue": f"Potentially vulnerable dependency: {pattern}",
                            "description": "Dependency may have known vulnerabilities",
                            "file": str(pyproject_file),
                            "recommendation": "Update to latest secure version"
                        })
        
        self.audit_results["findings"].extend(findings)
        
        for finding in findings:
            print(f"   {finding['severity']}: {finding['issue']}")
        
        if not findings:
            print("   ✅ No dependency security issues found")

    def _audit_configuration_security(self):
        """Audit configuration security."""
        print("\n⚙️ AUDITING CONFIGURATION SECURITY")
        print("-" * 30)
        
        findings = []
        
        # Check for debug mode in production
        config_file = self.project_root / "backend" / "app" / "core" / "config.py"
        if config_file.exists():
            with open(config_file) as f:
                content = f.read()
                
                if "DEBUG = True" in content:
                    findings.append({
                        "severity": "MEDIUM",
                        "category": "Configuration Security",
                        "issue": "Debug mode enabled",
                        "description": "Debug mode may expose sensitive information",
                        "file": str(config_file),
                        "recommendation": "Disable debug mode in production"
                    })
        
        self.audit_results["findings"].extend(findings)
        
        for finding in findings:
            print(f"   {finding['severity']}: {finding['issue']}")
        
        if not findings:
            print("   ✅ No configuration security issues found")

    def _generate_audit_report(self):
        """Generate final audit report."""
        print("\n" + "=" * 60)
        print("🔒 SECURITY AUDIT REPORT")
        print("=" * 60)
        
        # Count findings by severity
        critical_count = sum(1 for f in self.audit_results["findings"] if f["severity"] == "CRITICAL")
        high_count = sum(1 for f in self.audit_results["findings"] if f["severity"] == "HIGH")
        medium_count = sum(1 for f in self.audit_results["findings"] if f["severity"] == "MEDIUM")
        
        print(f"📊 FINDINGS SUMMARY:")
        print(f"   🚨 Critical: {critical_count}")
        print(f"   ⚠️ High: {high_count}")
        print(f"   📋 Medium: {medium_count}")
        print(f"   📈 Total: {len(self.audit_results['findings'])}")
        
        # Determine production readiness
        if critical_count > 0:
            self.audit_results["production_ready"] = False
            self.audit_results["risk_level"] = "CRITICAL"
            print(f"\n🚨 PRODUCTION READINESS: NOT READY")
            print(f"   Risk Level: CRITICAL")
            print(f"   Reason: {critical_count} critical security issues found")
        elif high_count > 0:
            self.audit_results["production_ready"] = False
            self.audit_results["risk_level"] = "HIGH"
            print(f"\n⚠️ PRODUCTION READINESS: CAUTION")
            print(f"   Risk Level: HIGH")
            print(f"   Reason: {high_count} high priority security issues found")
        elif medium_count > 0:
            self.audit_results["production_ready"] = True
            self.audit_results["risk_level"] = "MEDIUM"
            print(f"\n✅ PRODUCTION READINESS: ACCEPTABLE")
            print(f"   Risk Level: MEDIUM")
            print(f"   Note: {medium_count} medium priority issues should be addressed")
        else:
            self.audit_results["production_ready"] = True
            self.audit_results["risk_level"] = "LOW"
            print(f"\n🎉 PRODUCTION READINESS: READY")
            print(f"   Risk Level: LOW")
            print(f"   Status: All security checks passed")
        
        # Detailed findings
        if self.audit_results["findings"]:
            print(f"\n📋 DETAILED FINDINGS:")
            for i, finding in enumerate(self.audit_results["findings"], 1):
                print(f"\n   {i}. {finding['severity']}: {finding['issue']}")
                print(f"      Category: {finding['category']}")
                print(f"      Description: {finding['description']}")
                print(f"      File: {finding['file']}")
                print(f"      Recommendation: {finding['recommendation']}")
        
        # Security recommendations
        recommendations = [
            "Run security tests before every deployment",
            "Implement comprehensive logging and monitoring",
            "Set up security alerting for suspicious activity",
            "Regular security audits and penetration testing",
            "Keep all dependencies updated",
            "Implement proper backup and disaster recovery",
            "Set up intrusion detection system",
            "Regular security training for development team",
        ]
        
        print(f"\n🎯 SECURITY RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        print("\n" + "=" * 60)

    def _save_audit_results(self):
        """Save audit results to JSON file."""
        output_file = Path(__file__).parent / "security_audit_results.json"
        
        with open(output_file, 'w') as f:
            json.dump(self.audit_results, f, indent=2)
        
        print(f"📄 Audit results saved to: {output_file}")

    def run_security_tests(self):
        """Run the security test suite as part of audit."""
        print("\n🧪 RUNNING SECURITY TEST SUITE")
        print("-" * 30)
        
        try:
            # Run security tests
            result = subprocess.run([
                sys.executable, "run_security_tests.py"
            ], cwd=Path(__file__).parent, capture_output=True, text=True)
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Failed to run security tests: {e}")
            return False


def main():
    """Main entry point."""
    auditor = SecurityAuditor()
    
    print("Starting comprehensive security audit...")
    auditor.run_full_audit()
    
    print("\nRunning security test suite...")
    test_success = auditor.run_security_tests()
    
    # Final assessment
    if auditor.audit_results["production_ready"] and test_success:
        print("\n🎉 AUDIT COMPLETE: PRODUCTION READY")
        sys.exit(0)
    else:
        print("\n🚨 AUDIT COMPLETE: NOT PRODUCTION READY")
        sys.exit(1)


if __name__ == "__main__":
    main()
