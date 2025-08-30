#!/usr/bin/env python3
"""Security test runner with detailed reporting."""

import subprocess
import sys
import os
import json
from datetime import datetime
from pathlib import Path


class SecurityTestRunner:
    """Run security tests with comprehensive reporting."""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "critical_failures": [],
            "high_failures": [],
            "medium_failures": [],
            "vulnerabilities_found": [],
        }

    def run_tests(self, test_pattern: str = "test_*.py", verbose: bool = True):
        """Run security tests and generate report."""
        print("🔒 SECURITY TEST SUITE")
        print("=" * 50)
        print(f"Running tests in: {self.test_dir}")
        print(f"Pattern: {test_pattern}")
        print(f"Timestamp: {self.results['timestamp']}")
        print()

        # Build pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "-v" if verbose else "",
            "--tb=short",
            "--json-report",
            "--json-report-file=test_results.json",
            "-m", "not slow",  # Skip slow tests by default
        ]
        cmd = [arg for arg in cmd if arg]  # Remove empty strings

        try:
            # Run tests
            result = subprocess.run(
                cmd,
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Parse results
            self._parse_results(result)
            self._generate_report()
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("❌ CRITICAL: Tests timed out after 5 minutes!")
            return False
        except Exception as e:
            print(f"❌ CRITICAL: Test execution failed: {e}")
            return False

    def _parse_results(self, result):
        """Parse pytest results."""
        print("📊 TEST EXECUTION OUTPUT:")
        print("-" * 30)
        print(result.stdout)
        
        if result.stderr:
            print("\n⚠️ STDERR:")
            print(result.stderr)

        # Try to parse JSON report if available
        json_file = self.test_dir / "test_results.json"
        if json_file.exists():
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    self._extract_test_metrics(data)
            except Exception as e:
                print(f"Warning: Could not parse JSON report: {e}")

    def _extract_test_metrics(self, data):
        """Extract metrics from pytest JSON report."""
        summary = data.get("summary", {})
        self.results["total_tests"] = summary.get("total", 0)
        self.results["passed"] = summary.get("passed", 0)
        self.results["failed"] = summary.get("failed", 0)
        self.results["skipped"] = summary.get("skipped", 0)

        # Analyze failures by priority
        for test in data.get("tests", []):
            if test.get("outcome") == "failed":
                test_name = test.get("nodeid", "unknown")
                
                # Categorize by marker
                if "critical" in test_name:
                    self.results["critical_failures"].append(test_name)
                elif "high" in test_name:
                    self.results["high_failures"].append(test_name)
                else:
                    self.results["medium_failures"].append(test_name)

    def _generate_report(self):
        """Generate security test report."""
        print("\n" + "=" * 50)
        print("🔒 SECURITY TEST REPORT")
        print("=" * 50)
        
        # Summary
        print(f"📊 SUMMARY:")
        print(f"   Total Tests: {self.results['total_tests']}")
        print(f"   ✅ Passed: {self.results['passed']}")
        print(f"   ❌ Failed: {self.results['failed']}")
        print(f"   ⏭️ Skipped: {self.results['skipped']}")
        
        # Calculate pass rate
        if self.results['total_tests'] > 0:
            pass_rate = (self.results['passed'] / self.results['total_tests']) * 100
            print(f"   📈 Pass Rate: {pass_rate:.1f}%")

        # Critical failures
        if self.results['critical_failures']:
            print(f"\n🚨 CRITICAL FAILURES ({len(self.results['critical_failures'])}):")
            for failure in self.results['critical_failures']:
                print(f"   ❌ {failure}")

        # High priority failures
        if self.results['high_failures']:
            print(f"\n⚠️ HIGH PRIORITY FAILURES ({len(self.results['high_failures'])}):")
            for failure in self.results['high_failures']:
                print(f"   ❌ {failure}")

        # Medium priority failures
        if self.results['medium_failures']:
            print(f"\n⚠️ MEDIUM PRIORITY FAILURES ({len(self.results['medium_failures'])}):")
            for failure in self.results['medium_failures']:
                print(f"   ❌ {failure}")

        # Production readiness assessment
        print(f"\n🎯 PRODUCTION READINESS ASSESSMENT:")
        if self.results['critical_failures']:
            print("   ❌ NOT READY FOR PRODUCTION")
            print("   🚨 Critical security vulnerabilities found!")
            print("   🔧 Fix all critical issues before deployment")
        elif self.results['high_failures']:
            print("   ⚠️ CAUTION - High priority issues found")
            print("   🔧 Recommend fixing high priority issues")
        elif self.results['failed'] == 0:
            print("   ✅ READY FOR PRODUCTION")
            print("   🎉 All security tests passed!")
        else:
            print("   ⚠️ REVIEW REQUIRED")
            print("   📋 Some medium priority issues found")

        print("\n" + "=" * 50)

    def run_specific_category(self, category: str):
        """Run tests for a specific category."""
        test_file = f"test_{category}.py"
        if not (self.test_dir / test_file).exists():
            print(f"❌ Test file not found: {test_file}")
            return False
        
        print(f"🔒 Running {category.upper()} security tests...")
        return self.run_tests(test_file)


def main():
    """Main entry point."""
    runner = SecurityTestRunner()
    
    if len(sys.argv) > 1:
        category = sys.argv[1]
        success = runner.run_specific_category(category)
    else:
        success = runner.run_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
