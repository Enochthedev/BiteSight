#!/usr/bin/env python3
"""
Comprehensive security and privacy testing runner.
This script runs all security-related tests and generates a security report.
"""

import subprocess
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import argparse


class SecurityTestRunner:
    """Run comprehensive security and privacy tests."""

    def __init__(self):
        self.results = {
            "test_run_info": {
                "timestamp": datetime.utcnow().isoformat(),
                "python_version": sys.version,
                "test_categories": []
            },
            "test_results": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0
            },
            "security_issues": [],
            "recommendations": []
        }

    def run_test_category(self, category_name, test_file, description):
        """Run a specific category of security tests."""

        print(f"\n{'='*60}")
        print(f"Running {category_name}")
        print(f"Description: {description}")
        print(f"Test file: {test_file}")
        print(f"{'='*60}")

        start_time = time.time()

        try:
            # Run pytest with verbose output and JSON report
            cmd = [
                "python", "-m", "pytest",
                test_file,
                "-v",
                "--tb=short",
                "--json-report",
                f"--json-report-file=test_reports/{category_name}_report.json"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )

            end_time = time.time()
            duration = end_time - start_time

            # Parse results
            test_result = {
                "category": category_name,
                "description": description,
                "duration": duration,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "status": "PASSED" if result.returncode == 0 else "FAILED"
            }

            # Try to load JSON report if available
            json_report_path = Path(
                f"test_reports/{category_name}_report.json")
            if json_report_path.exists():
                try:
                    with open(json_report_path, 'r') as f:
                        json_report = json.load(f)
                        test_result["detailed_results"] = json_report

                        # Update summary
                        if "summary" in json_report:
                            summary = json_report["summary"]
                            self.results["summary"]["total_tests"] += summary.get(
                                "total", 0)
                            self.results["summary"]["passed"] += summary.get(
                                "passed", 0)
                            self.results["summary"]["failed"] += summary.get(
                                "failed", 0)
                            self.results["summary"]["skipped"] += summary.get(
                                "skipped", 0)
                            self.results["summary"]["errors"] += summary.get(
                                "error", 0)

                except Exception as e:
                    print(f"Warning: Could not parse JSON report: {e}")

            self.results["test_results"][category_name] = test_result
            self.results["test_run_info"]["test_categories"].append(
                category_name)

            # Print summary
            if result.returncode == 0:
                print(f"✅ {category_name} PASSED ({duration:.2f}s)")
            else:
                print(f"❌ {category_name} FAILED ({duration:.2f}s)")
                print(f"Error output: {result.stderr}")

            return result.returncode == 0

        except Exception as e:
            print(f"❌ Error running {category_name}: {e}")

            test_result = {
                "category": category_name,
                "description": description,
                "duration": 0,
                "return_code": -1,
                "error": str(e),
                "status": "ERROR"
            }

            self.results["test_results"][category_name] = test_result
            return False

    def analyze_security_issues(self):
        """Analyze test results for security issues."""

        security_issues = []
        recommendations = []

        for category, result in self.results["test_results"].items():
            if result["status"] == "FAILED":
                # Analyze failed tests for security implications

                if "authentication" in category.lower():
                    security_issues.append({
                        "category": "Authentication",
                        "severity": "HIGH",
                        "issue": f"Authentication security tests failed in {category}",
                        "description": "Authentication vulnerabilities detected"
                    })
                    recommendations.append({
                        "category": "Authentication",
                        "priority": "HIGH",
                        "recommendation": "Review and fix authentication security issues immediately"
                    })

                elif "privacy" in category.lower():
                    security_issues.append({
                        "category": "Privacy",
                        "severity": "HIGH",
                        "issue": f"Privacy compliance tests failed in {category}",
                        "description": "Privacy compliance violations detected"
                    })
                    recommendations.append({
                        "category": "Privacy",
                        "priority": "HIGH",
                        "recommendation": "Address privacy compliance issues before deployment"
                    })

                elif "penetration" in category.lower():
                    security_issues.append({
                        "category": "Penetration Testing",
                        "severity": "CRITICAL",
                        "issue": f"Penetration tests failed in {category}",
                        "description": "Security vulnerabilities detected through penetration testing"
                    })
                    recommendations.append({
                        "category": "Security",
                        "priority": "CRITICAL",
                        "recommendation": "Fix security vulnerabilities immediately before any deployment"
                    })

                elif "encryption" in category.lower():
                    security_issues.append({
                        "category": "Encryption",
                        "severity": "HIGH",
                        "issue": f"Encryption security tests failed in {category}",
                        "description": "Data encryption and storage security issues detected"
                    })
                    recommendations.append({
                        "category": "Encryption",
                        "priority": "HIGH",
                        "recommendation": "Review and strengthen data encryption mechanisms"
                    })

        # Add general recommendations
        if self.results["summary"]["failed"] > 0:
            recommendations.append({
                "category": "General",
                "priority": "HIGH",
                "recommendation": "Conduct security code review and fix all failing security tests"
            })

        if self.results["summary"]["total_tests"] == 0:
            security_issues.append({
                "category": "Testing",
                "severity": "MEDIUM",
                "issue": "No security tests were executed",
                "description": "Security testing coverage is insufficient"
            })
            recommendations.append({
                "category": "Testing",
                "priority": "MEDIUM",
                "recommendation": "Implement comprehensive security testing suite"
            })

        self.results["security_issues"] = security_issues
        self.results["recommendations"] = recommendations

    def generate_report(self, output_file="security_test_report.json"):
        """Generate comprehensive security test report."""

        # Analyze results
        self.analyze_security_issues()

        # Calculate additional metrics
        total_tests = self.results["summary"]["total_tests"]
        if total_tests > 0:
            pass_rate = (self.results["summary"]["passed"] / total_tests) * 100
            self.results["summary"]["pass_rate"] = round(pass_rate, 2)
        else:
            self.results["summary"]["pass_rate"] = 0

        # Security score (simple calculation)
        if total_tests > 0:
            security_score = max(
                0, 100 - (len(self.results["security_issues"]) * 10))
            self.results["summary"]["security_score"] = security_score
        else:
            self.results["summary"]["security_score"] = 0

        # Write report
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📊 Security test report generated: {output_file}")

        return self.results

    def print_summary(self):
        """Print test summary to console."""

        print(f"\n{'='*60}")
        print("SECURITY TEST SUMMARY")
        print(f"{'='*60}")

        summary = self.results["summary"]

        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print(f"Skipped: {summary['skipped']} ⏭️")
        print(f"Errors: {summary['errors']} 💥")
        print(f"Pass Rate: {summary.get('pass_rate', 0):.1f}%")
        print(f"Security Score: {summary.get('security_score', 0)}/100")

        # Print security issues
        if self.results["security_issues"]:
            print(
                f"\n🚨 SECURITY ISSUES DETECTED ({len(self.results['security_issues'])})")
            for issue in self.results["security_issues"]:
                severity_emoji = {
                    "CRITICAL": "🔴",
                    "HIGH": "🟠",
                    "MEDIUM": "🟡",
                    "LOW": "🟢"
                }.get(issue["severity"], "⚪")

                print(
                    f"  {severity_emoji} {issue['severity']}: {issue['issue']}")

        # Print recommendations
        if self.results["recommendations"]:
            print(
                f"\n💡 RECOMMENDATIONS ({len(self.results['recommendations'])})")
            for rec in self.results["recommendations"]:
                priority_emoji = {
                    "CRITICAL": "🔴",
                    "HIGH": "🟠",
                    "MEDIUM": "🟡",
                    "LOW": "🟢"
                }.get(rec["priority"], "⚪")

                print(
                    f"  {priority_emoji} {rec['priority']}: {rec['recommendation']}")

        print(f"\n{'='*60}")


def main():
    """Main function to run security tests."""

    parser = argparse.ArgumentParser(
        description="Run comprehensive security and privacy tests")
    parser.add_argument("--category", help="Run specific test category only")
    parser.add_argument(
        "--output", default="security_test_report.json", help="Output report file")
    parser.add_argument("--no-report", action="store_true",
                        help="Skip generating report file")

    args = parser.parse_args()

    # Create test reports directory
    Path("test_reports").mkdir(exist_ok=True)

    runner = SecurityTestRunner()

    # Define test categories
    test_categories = [
        {
            "name": "authentication_security",
            "file": "tests/test_security_authentication.py",
            "description": "Authentication and authorization security tests"
        },
        {
            "name": "privacy_compliance",
            "file": "tests/test_privacy_compliance.py",
            "description": "Privacy compliance and data protection tests"
        },
        {
            "name": "penetration_testing",
            "file": "tests/test_penetration_testing.py",
            "description": "Penetration testing for security vulnerabilities"
        },
        {
            "name": "data_encryption_security",
            "file": "tests/test_data_encryption_security.py",
            "description": "Data encryption and storage security tests"
        },
        {
            "name": "comprehensive_e2e",
            "file": "tests/test_comprehensive_e2e.py",
            "description": "Comprehensive end-to-end security workflows"
        },
        {
            "name": "performance_load",
            "file": "tests/test_performance_load.py",
            "description": "Performance and load testing for security implications"
        },
        {
            "name": "api_integration_comprehensive",
            "file": "tests/test_api_integration_comprehensive.py",
            "description": "Comprehensive API integration security tests"
        }
    ]

    print("🔒 Starting Comprehensive Security and Privacy Testing")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")

    # Run specific category or all categories
    if args.category:
        # Find and run specific category
        category = next(
            (cat for cat in test_categories if cat["name"] == args.category), None)
        if category:
            runner.run_test_category(
                category["name"], category["file"], category["description"])
        else:
            print(f"❌ Category '{args.category}' not found")
            print("Available categories:")
            for cat in test_categories:
                print(f"  - {cat['name']}: {cat['description']}")
            return 1
    else:
        # Run all categories
        for category in test_categories:
            runner.run_test_category(
                category["name"], category["file"], category["description"])

    # Generate report
    if not args.no_report:
        runner.generate_report(args.output)

    # Print summary
    runner.print_summary()

    # Return appropriate exit code
    if runner.results["summary"]["failed"] > 0 or runner.results["security_issues"]:
        print("\n❌ Security tests failed or security issues detected!")
        return 1
    else:
        print("\n✅ All security tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
