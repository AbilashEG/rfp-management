#!/usr/bin/env python3
"""
Local ZIP builder - for testing before CloudShell deployment
Creates correct Lambda ZIP structure with dependencies at root level
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path

def create_lambda_zip(lambda_name, source_files, deps_dir="package"):
    """Create a Lambda ZIP with correct structure"""
    
    print(f"\n{'='*80}")
    print(f"Building: {lambda_name}")
    print(f"{'='*80}")
    
    temp_dir = f"temp-{lambda_name}"
    zip_name = f"{lambda_name}.zip"
    
    # Clean up any existing temp directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    
    # Create temp directory
    os.makedirs(temp_dir)
    print(f"✓ Created temp directory: {temp_dir}")
    
    # Copy source files to root
    for source_file in source_files:
        if os.path.exists(source_file):
            dest = os.path.join(temp_dir, os.path.basename(source_file))
            shutil.copy2(source_file, dest)
            print(f"  ✓ Added: {os.path.basename(source_file)}")
        else:
            print(f"  ✗ MISSING: {source_file}")
            sys.exit(1)
    
    # Copy dependencies to temp directory (all files from package/)
    # This ensures they're at the root level in the ZIP
    if os.path.exists(deps_dir):
        for root, dirs, files in os.walk(deps_dir):
            for file in files:
                src = os.path.join(root, file)
                rel_path = os.path.relpath(src, deps_dir)
                dst = os.path.join(temp_dir, rel_path)
                
                # Create directories if needed
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
        
        file_count = sum([len(files) for _, _, files in os.walk(temp_dir)])
        print(f"  ✓ Added: {file_count} dependency files")
    else:
        print(f"  ! Warning: {deps_dir} not found")
    
    # Create ZIP
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zf.write(file_path, arcname)
    
    # Get size
    size_mb = os.path.getsize(zip_name) / (1024 * 1024)
    print(f"  ✓ Created: {zip_name} ({size_mb:.1f} MB)")
    
    # Verify structure
    with zipfile.ZipFile(zip_name, 'r') as zf:
        files_list = zf.namelist()
        has_python = any('site-packages' in f or f.startswith('bin/') for f in files_list)
        has_source = any(f.endswith('.py') and '/' not in f for f in files_list)
        
        if has_source and has_python:
            print(f"  ✅ Structure verified: [source files] + [python dependencies]")
        else:
            print(f"  ⚠️  Structure check: source={has_source}, deps={has_python}")
    
    # Cleanup
    shutil.rmtree(temp_dir)
    print(f"✓ Cleaned up temp directory")
    
    return zip_name


def main():
    print("\n" + "="*80)
    print("RFP Management System - Local ZIP Builder")
    print("="*80)
    
    # Check if dependencies are installed
    if not os.path.exists("package"):
        print("\n❌ ERROR: 'package' directory not found!")
        print("   Run: pip install -r RFP-main/requirements.txt -t package/")
        sys.exit(1)
    
    print("\nStep 1: Installing dependencies...")
    os.system("pip install -r RFP-main/requirements.txt -t package/ > /dev/null 2>&1")
    print("✓ Dependencies ready in package/")
    
    print("\nStep 2: Building Lambda ZIPs...")
    
    # Define all Lambda functions and their source files
    lambdas = {
        "orchestrator": [
            "RFP-main/agentcore_orchestrator.py",
            "RFP-main/agentcore_memory.py",
            "RFP-main/config.py"
        ],
        "supplier_lookup_tool": [
            "RFP-main/lambda/supplier_lookup_lambda.py",
            "RFP-main/config.py"
        ],
        "rfp_generator_tool": [
            "RFP-main/lambda/rfp_generator_lambda.py",
            "RFP-main/config.py"
        ],
        "email_dispatch_tool": [
            "RFP-main/lambda/email_dispatch_lambda.py",
            "RFP-main/config.py"
        ],
        "proposal_fetch_tool": [
            "RFP-main/lambda/proposal_fetch_lambda.py",
            "RFP-main/config.py"
        ],
        "scoring_tool": [
            "RFP-main/lambda/scoring_lambda.py",
            "RFP-main/config.py"
        ],
        "recommendation_tool": [
            "RFP-main/lambda/recommendation_lambda.py",
            "RFP-main/config.py"
        ]
    }
    
    created_zips = []
    for lambda_name, source_files in lambdas.items():
        zip_file = create_lambda_zip(lambda_name, source_files)
        created_zips.append(zip_file)
    
    print("\n" + "="*80)
    print("✅ BUILD COMPLETE!")
    print("="*80)
    print(f"\n✓ Created {len(created_zips)} Lambda ZIPs:\n")
    for zip_file in created_zips:
        if os.path.exists(zip_file):
            size_mb = os.path.getsize(zip_file) / (1024 * 1024)
            print(f"  {zip_file} ({size_mb:.1f} MB)")
    
    print("\n📋 Next Steps:")
    print("   1. Verify ZIP files are in current directory")
    print("   2. Copy all .zip files to CloudShell")
    print("   3. Run: bash cloudshell-deploy.sh")
    print("\n")


if __name__ == "__main__":
    main()
