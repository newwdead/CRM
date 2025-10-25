#!/usr/bin/env python3
import os
import re

print("=" * 60)
print("SECURITY ISSUES CHECK")
print("=" * 60)

issues = []

# Check 1: SQL Injection risks
print("\n1. Checking for SQL injection risks...")
sql_patterns = [r'execute\([^)]*%', r'\.format\(.*sql', r'f".*SELECT.*{']
backend_files = []
for root, dirs, files in os.walk('backend/app'):
    for file in files:
        if file.endswith('.py'):
            backend_files.append(os.path.join(root, file))

sql_issues = 0
for filepath in backend_files:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        for pattern in sql_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                sql_issues += 1
                issues.append(f"Potential SQL injection: {filepath}")
                break

print(f"   Found {sql_issues} potential SQL injection risks")

# Check 2: eval() usage
print("\n2. Checking for eval() usage...")
eval_count = 0
for filepath in backend_files:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        if 'eval(' in f.read():
            eval_count += 1
            issues.append(f"Dangerous eval() usage: {filepath}")

print(f"   Found {eval_count} eval() usages")

# Check 3: exec() usage
print("\n3. Checking for exec() usage...")
exec_count = 0
for filepath in backend_files:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        if 'exec(' in f.read():
            exec_count += 1
            issues.append(f"Dangerous exec() usage: {filepath}")

print(f"   Found {exec_count} exec() usages")

# Check 4: Debug mode in production
print("\n4. Checking for debug mode...")
debug_issues = 0
for filepath in backend_files:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        if re.search(r'debug\s*=\s*True', content, re.IGNORECASE):
            debug_issues += 1
            issues.append(f"Debug mode enabled: {filepath}")

print(f"   Found {debug_issues} debug mode issues")

# Check 5: Weak crypto
print("\n5. Checking for weak cryptography...")
weak_crypto = 0
for filepath in backend_files:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        if re.search(r'md5|sha1(?!rsa)', content, re.IGNORECASE):
            weak_crypto += 1
            issues.append(f"Weak cryptography (MD5/SHA1): {filepath}")

print(f"   Found {weak_crypto} weak crypto usages")

# Check 6: Unvalidated redirects
print("\n6. Checking for unvalidated redirects...")
redirect_issues = 0
for filepath in backend_files:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        if re.search(r'redirect\([^)]*request\.|location\s*=\s*request\.', content):
            redirect_issues += 1
            issues.append(f"Potential unvalidated redirect: {filepath}")

print(f"   Found {redirect_issues} redirect issues")

print("\n" + "=" * 60)
print(f"TOTAL ISSUES FOUND: {len(issues)}")
print("=" * 60)

if issues:
    print("\nDETAILS:")
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue}")
else:
    print("\n✅ No major security issues found!")

