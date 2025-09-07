#!/usr/bin/env node

/**
 * Mobile app security testing runner
 * Runs security-focused tests for the React Native application
 */

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

class MobileSecurityTestRunner {
    constructor() {
        this.results = {
            testRunInfo: {
                timestamp: new Date().toISOString(),
                nodeVersion: process.version,
                testCategories: []
            },
            testResults: {},
            summary: {
                totalTests: 0,
                passed: 0,
                failed: 0,
                skipped: 0
            },
            securityIssues: [],
            recommendations: []
        };
    }

    async runTestCategory(categoryName, testPattern, description) {
        console.log(`\n${'='.repeat(60)}`);
        console.log(`Running ${categoryName}`);
        console.log(`Description: ${description}`);
        console.log(`Test pattern: ${testPattern}`);
        console.log(`${'='.repeat(60)}`);

        const startTime = Date.now();

        try {
            // Run Jest with specific test pattern
            const jestCmd = [
                'npx', 'jest',
                testPattern,
                '--verbose',
                '--json',
                '--outputFile', `test-reports/${categoryName}-report.json`,
                '--coverage',
                '--coverageDirectory', `test-reports/${categoryName}-coverage`
            ];

            const result = execSync(jestCmd.join(' '), {
                encoding: 'utf8',
                stdio: 'pipe'
            });

            const endTime = Date.now();
            const duration = (endTime - startTime) / 1000;

            const testResult = {
                category: categoryName,
                description: description,
                duration: duration,
                status: 'PASSED',
                output: result
            };

            // Try to load JSON report
            const reportPath = path.join('test-reports', `${categoryName}-report.json`);
            if (fs.existsSync(reportPath)) {
                try {
                    const jsonReport = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
                    testResult.detailedResults = jsonReport;

                    // Update summary
                    if (jsonReport.numTotalTests) {
                        this.results.summary.totalTests += jsonReport.numTotalTests;
                        this.results.summary.passed += jsonReport.numPassedTests;
                        this.results.summary.failed += jsonReport.numFailedTests;
                        this.results.summary.skipped += jsonReport.numPendingTests;
                    }
                } catch (e) {
                    console.warn(`Warning: Could not parse JSON report: ${e.message}`);
                }
            }

            this.results.testResults[categoryName] = testResult;
            this.results.testRunInfo.testCategories.push(categoryName);

            console.log(`✅ ${categoryName} PASSED (${duration.toFixed(2)}s)`);
            return true;

        } catch (error) {
            const endTime = Date.now();
            const duration = (endTime - startTime) / 1000;

            const testResult = {
                category: categoryName,
                description: description,
                duration: duration,
                status: 'FAILED',
                error: error.message,
                output: error.stdout || '',
                stderr: error.stderr || ''
            };

            this.results.testResults[categoryName] = testResult;

            console.log(`❌ ${categoryName} FAILED (${duration.toFixed(2)}s)`);
            console.log(`Error: ${error.message}`);
            return false;
        }
    }

    analyzeSecurityIssues() {
        const securityIssues = [];
        const recommendations = [];

        for (const [category, result] of Object.entries(this.results.testResults)) {
            if (result.status === 'FAILED') {
                if (category.includes('security') || category.includes('auth')) {
                    securityIssues.push({
                        category: 'Mobile Security',
                        severity: 'HIGH',
                        issue: `Security tests failed in ${category}`,
                        description: 'Mobile security vulnerabilities detected'
                    });
                    recommendations.push({
                        category: 'Mobile Security',
                        priority: 'HIGH',
                        recommendation: 'Review and fix mobile security issues immediately'
                    });
                }

                if (category.includes('privacy') || category.includes('data')) {
                    securityIssues.push({
                        category: 'Data Privacy',
                        severity: 'HIGH',
                        issue: `Privacy tests failed in ${category}`,
                        description: 'Mobile data privacy issues detected'
                    });
                    recommendations.push({
                        category: 'Data Privacy',
                        priority: 'HIGH',
                        recommendation: 'Address mobile data privacy issues'
                    });
                }
            }
        }

        // Check for security-specific issues
        this.checkForCommonMobileSecurityIssues(securityIssues, recommendations);

        this.results.securityIssues = securityIssues;
        this.results.recommendations = recommendations;
    }

    checkForCommonMobileSecurityIssues(securityIssues, recommendations) {
        // Check package.json for known vulnerable dependencies
        try {
            const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));

            // Check for potentially insecure dependencies
            const insecureDeps = [
                'react-native-webview', // If using old versions
                'react-native-camera',  // If using deprecated versions
            ];

            const allDeps = { ...packageJson.dependencies, ...packageJson.devDependencies };

            for (const dep of insecureDeps) {
                if (allDeps[dep]) {
                    securityIssues.push({
                        category: 'Dependencies',
                        severity: 'MEDIUM',
                        issue: `Potentially insecure dependency: ${dep}`,
                        description: 'Review dependency for security vulnerabilities'
                    });
                }
            }
        } catch (e) {
            console.warn('Could not analyze package.json for security issues');
        }

        // Check for hardcoded secrets in source files
        this.checkForHardcodedSecrets(securityIssues, recommendations);
    }

    checkForHardcodedSecrets(securityIssues, recommendations) {
        const secretPatterns = [
            /api[_-]?key[_-]?=.{10,}/i,
            /secret[_-]?key[_-]?=.{10,}/i,
            /password[_-]?=.{5,}/i,
            /token[_-]?=.{10,}/i,
            /auth[_-]?key[_-]?=.{10,}/i
        ];

        const sourceFiles = this.getSourceFiles('src');

        for (const file of sourceFiles) {
            try {
                const content = fs.readFileSync(file, 'utf8');

                for (const pattern of secretPatterns) {
                    if (pattern.test(content)) {
                        securityIssues.push({
                            category: 'Hardcoded Secrets',
                            severity: 'HIGH',
                            issue: `Potential hardcoded secret in ${file}`,
                            description: 'Hardcoded secrets detected in source code'
                        });

                        recommendations.push({
                            category: 'Secrets Management',
                            priority: 'HIGH',
                            recommendation: 'Remove hardcoded secrets and use secure configuration'
                        });
                        break; // Only report once per file
                    }
                }
            } catch (e) {
                // Skip files that can't be read
            }
        }
    }

    getSourceFiles(dir, files = []) {
        const items = fs.readdirSync(dir);

        for (const item of items) {
            const fullPath = path.join(dir, item);
            const stat = fs.statSync(fullPath);

            if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
                this.getSourceFiles(fullPath, files);
            } else if (stat.isFile() && (item.endsWith('.js') || item.endsWith('.ts') || item.endsWith('.tsx'))) {
                files.push(fullPath);
            }
        }

        return files;
    }

    generateReport(outputFile = 'mobile-security-report.json') {
        this.analyzeSecurityIssues();

        // Calculate metrics
        const { totalTests, passed } = this.results.summary;
        if (totalTests > 0) {
            this.results.summary.passRate = Math.round((passed / totalTests) * 100 * 100) / 100;
        } else {
            this.results.summary.passRate = 0;
        }

        // Security score
        const securityScore = Math.max(0, 100 - (this.results.securityIssues.length * 10));
        this.results.summary.securityScore = securityScore;

        // Write report
        fs.writeFileSync(outputFile, JSON.stringify(this.results, null, 2));
        console.log(`\n📊 Mobile security test report generated: ${outputFile}`);

        return this.results;
    }

    printSummary() {
        console.log(`\n${'='.repeat(60)}`);
        console.log('MOBILE SECURITY TEST SUMMARY');
        console.log(`${'='.repeat(60)}`);

        const { summary } = this.results;

        console.log(`Total Tests: ${summary.totalTests}`);
        console.log(`Passed: ${summary.passed} ✅`);
        console.log(`Failed: ${summary.failed} ❌`);
        console.log(`Skipped: ${summary.skipped} ⏭️`);
        console.log(`Pass Rate: ${summary.passRate || 0}%`);
        console.log(`Security Score: ${summary.securityScore || 0}/100`);

        // Print security issues
        if (this.results.securityIssues.length > 0) {
            console.log(`\n🚨 SECURITY ISSUES DETECTED (${this.results.securityIssues.length})`);
            for (const issue of this.results.securityIssues) {
                const severityEmoji = {
                    'CRITICAL': '🔴',
                    'HIGH': '🟠',
                    'MEDIUM': '🟡',
                    'LOW': '🟢'
                }[issue.severity] || '⚪';

                console.log(`  ${severityEmoji} ${issue.severity}: ${issue.issue}`);
            }
        }

        // Print recommendations
        if (this.results.recommendations.length > 0) {
            console.log(`\n💡 RECOMMENDATIONS (${this.results.recommendations.length})`);
            for (const rec of this.results.recommendations) {
                const priorityEmoji = {
                    'CRITICAL': '🔴',
                    'HIGH': '🟠',
                    'MEDIUM': '🟡',
                    'LOW': '🟢'
                }[rec.priority] || '⚪';

                console.log(`  ${priorityEmoji} ${rec.priority}: ${rec.recommendation}`);
            }
        }

        console.log(`\n${'='.repeat(60)}`);
    }

    async runSecurityAudit() {
        console.log('\n🔍 Running npm security audit...');

        try {
            const auditResult = execSync('npm audit --json', { encoding: 'utf8' });
            const audit = JSON.parse(auditResult);

            if (audit.vulnerabilities && Object.keys(audit.vulnerabilities).length > 0) {
                console.log(`⚠️  Found ${Object.keys(audit.vulnerabilities).length} vulnerabilities`);

                for (const [pkg, vuln] of Object.entries(audit.vulnerabilities)) {
                    if (vuln.severity === 'high' || vuln.severity === 'critical') {
                        this.results.securityIssues.push({
                            category: 'Dependencies',
                            severity: vuln.severity.toUpperCase(),
                            issue: `Vulnerable dependency: ${pkg}`,
                            description: vuln.title || 'Security vulnerability in dependency'
                        });
                    }
                }
            } else {
                console.log('✅ No vulnerabilities found in dependencies');
            }
        } catch (error) {
            console.log('⚠️  Could not run security audit:', error.message);
        }
    }
}

async function main() {
    const args = process.argv.slice(2);
    const category = args.find(arg => arg.startsWith('--category='))?.split('=')[1];
    const output = args.find(arg => arg.startsWith('--output='))?.split('=')[1] || 'mobile-security-report.json';
    const noReport = args.includes('--no-report');

    // Create test reports directory
    if (!fs.existsSync('test-reports')) {
        fs.mkdirSync('test-reports');
    }

    const runner = new MobileSecurityTestRunner();

    // Define test categories
    const testCategories = [
        {
            name: 'authentication_security',
            pattern: '__tests__/**/auth/*.test.{js,ts,tsx}',
            description: 'Authentication and authorization security tests'
        },
        {
            name: 'data_privacy',
            pattern: '__tests__/**/privacy/*.test.{js,ts,tsx}',
            description: 'Data privacy and protection tests'
        },
        {
            name: 'network_security',
            pattern: '__tests__/**/services/*security*.test.{js,ts,tsx}',
            description: 'Network communication security tests'
        },
        {
            name: 'storage_security',
            pattern: '__tests__/**/storage/*.test.{js,ts,tsx}',
            description: 'Local storage security tests'
        },
        {
            name: 'e2e_security_workflows',
            pattern: '__tests__/e2e/*security*.test.{js,ts,tsx}',
            description: 'End-to-end security workflow tests'
        },
        {
            name: 'complete_user_workflows',
            pattern: '__tests__/e2e/complete-user-workflows.test.tsx',
            description: 'Complete user workflow security tests'
        }
    ];

    console.log('🔒 Starting Mobile Security Testing');
    console.log(`Timestamp: ${new Date().toISOString()}`);

    // Run security audit first
    await runner.runSecurityAudit();

    // Run specific category or all categories
    if (category) {
        const testCategory = testCategories.find(cat => cat.name === category);
        if (testCategory) {
            await runner.runTestCategory(testCategory.name, testCategory.pattern, testCategory.description);
        } else {
            console.log(`❌ Category '${category}' not found`);
            console.log('Available categories:');
            for (const cat of testCategories) {
                console.log(`  - ${cat.name}: ${cat.description}`);
            }
            process.exit(1);
        }
    } else {
        // Run all categories
        for (const testCategory of testCategories) {
            await runner.runTestCategory(testCategory.name, testCategory.pattern, testCategory.description);
        }
    }

    // Generate report
    if (!noReport) {
        runner.generateReport(output);
    }

    // Print summary
    runner.printSummary();

    // Exit with appropriate code
    if (runner.results.summary.failed > 0 || runner.results.securityIssues.length > 0) {
        console.log('\n❌ Mobile security tests failed or security issues detected!');
        process.exit(1);
    } else {
        console.log('\n✅ All mobile security tests passed!');
        process.exit(0);
    }
}

if (require.main === module) {
    main().catch(error => {
        console.error('Error running mobile security tests:', error);
        process.exit(1);
    });
}

module.exports = { MobileSecurityTestRunner };