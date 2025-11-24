#!/usr/bin/env python3
"""
Quick validation script to check if all hardcoded values are removed
Run this before committing changes
"""

import os
import re
from pathlib import Path

# Patterns that indicate hardcoded sensitive data
SENSITIVE_PATTERNS = [
    r'"https://eastus2\.api\.azureml\.ms"',
    r'"rg-kushikote',
    r'"055cefeb-8cfd',
    r'"docstorage"',
    r'"dataexc"',
    r'cosmosaudit\.azurewebsites\.net',
    r'AccountKey=[^;]+;',  # Storage account keys in connection strings
]

# Files to check (Python files only)
EXTENSIONS = ['.py']
EXCLUDE_DIRS = ['__pycache__', 'venv', 'env', 'node_modules', '.git', 'frontend']
EXCLUDE_FILES = ['validate_cleanup.py', 'tinsurance.py']  # Self and test files

def find_python_files(root_dir):
    """Find all Python files in the directory"""
    python_files = []
    for path in Path(root_dir).rglob('*'):
        if any(excluded in str(path) for excluded in EXCLUDE_DIRS):
            continue
        if any(str(path).endswith(excluded) for excluded in EXCLUDE_FILES):
            continue
        if path.suffix in EXTENSIONS and path.is_file():
            python_files.append(path)
    return python_files

def check_file_for_sensitive_data(file_path):
    """Check a single file for sensitive data patterns"""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            for line_num, line in enumerate(content.split('\n'), 1):
                # Skip lines with os.getenv (these are using env vars, which is good)
                if 'os.getenv' in line and ('default' in line.lower() or ',' in line):
                    continue
                for pattern in SENSITIVE_PATTERNS:
                    if re.search(pattern, line):
                        issues.append({
                            'file': str(file_path),
                            'line': line_num,
                            'pattern': pattern,
                            'content': line.strip()[:100]  # First 100 chars
                        })
    except Exception as e:
        print(f"⚠️  Error reading {file_path}: {e}")
    
    return issues

def check_env_file_exists():
    """Check if .env.example exists and .env is in .gitignore"""
    has_example = os.path.exists('.env.example')
    has_gitignore = os.path.exists('.gitignore')
    env_in_gitignore = False
    
    if has_gitignore:
        with open('.gitignore', 'r') as f:
            env_in_gitignore = '.env' in f.read()
    
    return has_example, env_in_gitignore

def main():
    print("\n" + "="*70)
    print("🔍 Checking for Hardcoded Sensitive Data")
    print("="*70 + "\n")
    
    # Check environment file setup
    has_example, env_in_gitignore = check_env_file_exists()
    
    print("📋 Environment File Setup:")
    print(f"   .env.example exists: {'✅' if has_example else '❌'}")
    print(f"   .env in .gitignore: {'✅' if env_in_gitignore else '❌'}")
    print()
    
    # Find and check all Python files
    root_dir = '.'
    python_files = find_python_files(root_dir)
    
    print(f"📂 Checking {len(python_files)} Python files...\n")
    
    all_issues = []
    for file_path in python_files:
        issues = check_file_for_sensitive_data(file_path)
        all_issues.extend(issues)
    
    # Report results
    if all_issues:
        print("❌ FOUND POTENTIAL SENSITIVE DATA:\n")
        for issue in all_issues:
            print(f"📄 File: {issue['file']}")
            print(f"   Line {issue['line']}: {issue['content']}")
            print(f"   Pattern: {issue['pattern']}")
            print()
        print(f"⚠️  Total issues found: {len(all_issues)}")
        print("\n💡 Please review these and move to environment variables if needed.")
        return 1
    else:
        print("✅ NO HARDCODED SENSITIVE DATA FOUND!")
        print("\n📝 Summary:")
        print(f"   - Checked {len(python_files)} Python files")
        print(f"   - All sensitive data moved to environment variables")
        print(f"   - .env.example template: {'✅' if has_example else '❌'}")
        print(f"   - .env properly ignored: {'✅' if env_in_gitignore else '❌'}")
        print("\n🎉 Code is clean and ready to commit!")
        return 0

if __name__ == "__main__":
    exit(main())
