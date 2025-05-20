#!/usr/bin/env python3
"""
API Import Scanner

This script scans your codebase to find any direct imports from 
mysite/provider/api/ or mysite/patient/api/.

Usage:
    python api_import_scanner.py /path/to/your/codebase
"""

import os
import re
import sys
import ast
from pathlib import Path
from typing import List, Dict, Set, Tuple

# Patterns to look for in imports
PROVIDER_API_PATTERN = re.compile(r'(from|import)\s+(mysite\.)?provider\.api')
PATIENT_API_PATTERN = re.compile(r'(from|import)\s+(mysite\.)?patient\.api')

# AST patterns to check for more accurate import detection
class ImportVisitor(ast.NodeVisitor):
    def __init__(self):
        self.provider_api_imports = []
        self.patient_api_imports = []
        
    def visit_Import(self, node):
        for name in node.names:
            if 'provider.api' in name.name:
                self.provider_api_imports.append(f"import {name.name}")
            if 'patient.api' in name.name:
                self.patient_api_imports.append(f"import {name.name}")
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        module = node.module or ""
        if 'provider.api' in module:
            imports = ", ".join(name.name for name in node.names)
            self.provider_api_imports.append(f"from {module} import {imports}")
        if 'patient.api' in module:
            imports = ", ".join(name.name for name in node.names)
            self.patient_api_imports.append(f"from {module} import {imports}")
        self.generic_visit(node)

def scan_file_for_imports(file_path: Path) -> Tuple[List[str], List[str]]:
    """Scan a single file for provider/patient API imports using both regex and AST."""
    provider_imports = []
    patient_imports = []
    
    # Skip files that are too large to avoid performance issues
    if file_path.stat().st_size > 1024 * 1024:  # Skip files larger than 1MB
        print(f"Skipping large file: {file_path}")
        return provider_imports, patient_imports
    
    # First check with regex (faster, but less accurate)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for regex patterns
        provider_matches = PROVIDER_API_PATTERN.findall(content)
        patient_matches = PATIENT_API_PATTERN.findall(content)
        
        # If we found potential matches, do a more accurate AST check
        if provider_matches or patient_matches:
            try:
                tree = ast.parse(content)
                visitor = ImportVisitor()
                visitor.visit(tree)
                provider_imports = visitor.provider_api_imports
                patient_imports = visitor.patient_api_imports
            except SyntaxError:
                # If AST parsing fails, fall back to the regex results
                provider_imports = [f"{match[0]} {match[1]}provider.api" for match in provider_matches]
                patient_imports = [f"{match[0]} {match[1]}patient.api" for match in patient_matches]
    except (UnicodeDecodeError, IOError) as e:
        print(f"Error reading {file_path}: {e}")
    
    return provider_imports, patient_imports

def scan_directory(directory: Path) -> Dict[str, Dict[str, List[str]]]:
    """Scan a directory recursively for provider/patient API imports."""
    results = {}
    
    for root, dirs, files in os.walk(directory):
        # Skip virtual environments, node_modules, __pycache__, etc.
        dirs[:] = [d for d in dirs if not d.startswith('.') and 
                   d not in ['venv', 'env', 'node_modules', '__pycache__', 'migrations']]
        
        for file in files:
            if not file.endswith('.py'):
                continue
                
            file_path = Path(root) / file
            provider_imports, patient_imports = scan_file_for_imports(file_path)
            
            if provider_imports or patient_imports:
                results[str(file_path)] = {
                    'provider_api': provider_imports,
                    'patient_api': patient_imports
                }
    
    return results

def print_results(results: Dict[str, Dict[str, List[str]]]):
    """Print the scan results in a formatted way."""
    if not results:
        print("No direct imports from provider.api or patient.api found!")
        return
    
    print("\n==== Files with Direct API Imports ====\n")
    
    provider_count = 0
    patient_count = 0
    
    for file_path, imports in results.items():
        has_imports = False
        
        if imports['provider_api']:
            if not has_imports:
                print(f"\n📁 {file_path}")
                has_imports = True
            print("   Provider API imports:")
            for imp in imports['provider_api']:
                print(f"     - {imp}")
                provider_count += 1
        
        if imports['patient_api']:
            if not has_imports:
                print(f"\n📁 {file_path}")
            print("   Patient API imports:")
            for imp in imports['patient_api']:
                print(f"     - {imp}")
                patient_count += 1
    
    print("\n==== Summary ====")
    print(f"Total files with direct imports: {len(results)}")
    print(f"Total provider.api imports: {provider_count}")
    print(f"Total patient.api imports: {patient_count}")
    
    if provider_count or patient_count:
        print("\n❗ Direct imports found. Consider updating these imports to use the versioned API.")
    else:
        print("\n✅ No direct imports found. It should be safe to remove the old API directories.")

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} /path/to/your/codebase")
        sys.exit(1)
    
    directory = Path(sys.argv[1])
    if not directory.is_dir():
        print(f"Error: {directory} is not a valid directory")
        sys.exit(1)
    
    print(f"Scanning {directory} for direct imports from provider.api and patient.api...")
    results = scan_directory(directory)
    print_results(results)

if __name__ == "__main__":
    main()
