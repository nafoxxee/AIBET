#!/usr/bin/env python3
"""
Git setup script for AI BET Analytics Platform
"""

import os
import subprocess
import sys

def run_command(command, cwd=None):
    """Run shell command and return result"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def setup_git_repo():
    """Setup Git repository and push to GitHub"""
    print("🔧 Setting up Git repository...")
    
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"📁 Working directory: {current_dir}")
    
    # Initialize git repo
    print("📦 Initializing Git repository...")
    success, stdout, stderr = run_command("git init", current_dir)
    if not success:
        print(f"❌ Git init failed: {stderr}")
        return False
    print("✅ Git repository initialized")
    
    # Add all files
    print("📋 Adding files to Git...")
    success, stdout, stderr = run_command("git add .", current_dir)
    if not success:
        print(f"❌ Git add failed: {stderr}")
        return False
    print("✅ Files added to Git")
    
    # Initial commit
    print("💾 Creating initial commit...")
    success, stdout, stderr = run_command('git commit -m "Initial commit: AI BET Analytics Platform"', current_dir)
    if not success:
        print(f"❌ Git commit failed: {stderr}")
        return False
    print("✅ Initial commit created")
    
    # Add remote
    print("🔗 Adding remote repository...")
    success, stdout, stderr = run_command("git remote add origin https://github.com/nafoxxee/AIBET.git", current_dir)
    if not success:
        print(f"❌ Git remote add failed: {stderr}")
        return False
    print("✅ Remote repository added")
    
    # Push to GitHub
    print("📤 Pushing to GitHub...")
    success, stdout, stderr = run_command("git push -u origin main", current_dir)
    if not success:
        print(f"❌ Git push failed: {stderr}")
        print("💡 You may need to authenticate with GitHub first")
        return False
    print("✅ Code pushed to GitHub!")
    
    return True

def main():
    print("🚀 AI BET Analytics - Git Setup")
    print("=" * 50)
    
    if setup_git_repo():
        print("\n🎉 Git repository setup complete!")
        print("📍 Repository: https://github.com/nafoxxee/AIBET.git")
        print("📱 The project is now available on GitHub!")
    else:
        print("\n❌ Git setup failed. Please check the error messages above.")
        print("💡 You may need to:")
        print("   1. Install Git: https://git-scm.com/")
        print("   2. Authenticate with GitHub")
        print("   3. Check repository permissions")

if __name__ == "__main__":
    main()
