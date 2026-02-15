#!/bin/bash
#============================================
# GITHUB SETUP - AUTOMATED WITH PYTHON API
# Alternative using GitHub REST API
#============================================

set -e

REPO_OWNER="hellyparmar"
REPO_NAME="R-DIOS"
GITHUB_TOKEN="${GITHUB_TOKEN}"

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                    GITHUB SETUP - PYTHON API                      ║"
echo "║        Enterprise Retail Intelligence System - Phase 0             ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if token is provided
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN environment variable not set"
    echo ""
    echo "To authenticate, you need a Personal Access Token:"
    echo ""
    echo "Steps to create a token:"
    echo "  1. Go to: https://github.com/settings/tokens"
    echo "  2. Click 'Generate new token (classic)'"
    echo "  3. Select scopes:"
    echo "     - repo (all)"
    echo "     - read:org"
    echo "  4. Generate and copy the token"
    echo ""
    echo "Then run:"
    echo "  export GITHUB_TOKEN='your_token_here'"
    echo "  ./PHASE_0_IMPLEMENTATION/GITHUB_SETUP_PYTHON.sh"
    echo ""
    exit 1
fi

echo "✅ GitHub token found"
echo ""

# Create Python script for GitHub API calls
cat > /tmp/github_setup.py << 'PYTHON_EOF'
#!/usr/bin/env python3

import os
import json
import requests
from pathlib import Path

REPO_OWNER = "hellyparmar"
REPO_NAME = "R-DIOS"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def create_milestone():
    """Create Phase 0 milestone"""
    print("📝 Creating milestone: Phase 0 - Critical Blockers")
    
    milestone_data = {
        "title": "Phase 0 - Critical Blockers",
        "description": "Database migration, configuration, pagination, and testing - Feb 17-20, 2026",
        "due_on": "2026-02-20T23:59:59Z"
    }
    
    response = requests.post(
        f"{BASE_URL}/milestones",
        headers=HEADERS,
        json=milestone_data
    )
    
    if response.status_code == 201:
        milestone = response.json()
        print(f"✅ Milestone created (ID: {milestone['number']})")
        return milestone['number']
    elif response.status_code == 422:
        print("⚠️  Milestone already exists")
        # Get existing milestone
        milestones = requests.get(
            f"{BASE_URL}/milestones",
            headers=HEADERS
        ).json()
        for m in milestones:
            if m['title'] == "Phase 0 - Critical Blockers":
                return m['number']
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def create_labels():
    """Create GitHub labels"""
    print("\n📝 Creating labels...")
    
    labels = [
        {"name": "task/database", "color": "0366d6", "description": "Database-related tasks"},
        {"name": "task/config", "color": "0366d6", "description": "Configuration tasks"},
        {"name": "task/pagination", "color": "0366d6", "description": "Pagination implementation"},
        {"name": "task/testing", "color": "0366d6", "description": "Testing and QA"},
        {"name": "task/deployment", "color": "0366d6", "description": "Deployment and gate approval"},
        {"name": "priority/critical", "color": "d73a49", "description": "Blocks Phase 1"},
        {"name": "priority/high", "color": "a2eeef", "description": "Important but not blocking"},
        {"name": "status/in-progress", "color": "fbca04", "description": "Currently being worked on"},
    ]
    
    created_count = 0
    for label in labels:
        response = requests.post(
            f"{BASE_URL}/labels",
            headers=HEADERS,
            json=label
        )
        
        if response.status_code == 201:
            print(f"  ✅ {label['name']}")
            created_count += 1
        elif response.status_code == 422:
            print(f"  ⚠️  {label['name']} (already exists)")
        else:
            print(f"  ❌ {label['name']}: {response.status_code}")
    
    print(f"✅ Labels setup complete ({created_count} created/updated)")

def import_issues(milestone_number):
    """Import GitHub issues from markdown files"""
    print("\n📝 Importing GitHub issues...")
    
    issues_dir = Path("./PHASE_0_IMPLEMENTATION/github_issues")
    
    if not issues_dir.exists():
        print(f"❌ Issues directory not found: {issues_dir}")
        return
    
    issue_files = sorted(issues_dir.glob("ISSUE_*.md"))
    print(f"Found {len(issue_files)} issue files")
    
    for idx, issue_file in enumerate(issue_files, 1):
        filename = issue_file.name
        title = filename.replace("ISSUE_", "").replace(".md", "").replace("_", " ")
        
        with open(issue_file, 'r') as f:
            body = f.read()
        
        issue_data = {
            "title": title,
            "body": body,
            "labels": ["priority/critical"],
            "milestone": milestone_number
        }
        
        response = requests.post(
            f"{BASE_URL}/issues",
            headers=HEADERS,
            json=issue_data
        )
        
        if response.status_code == 201:
            issue = response.json()
            print(f"  ✅ Issue #{issue['number']}: {title}")
        elif response.status_code == 422:
            print(f"  ⚠️  Issue already exists: {title}")
        else:
            print(f"  ❌ Error: {response.status_code} - {title}")
    
    print(f"✅ Issues import complete")

def main():
    print("Starting GitHub setup...\n")
    
    # Create milestone
    milestone_number = create_milestone()
    if not milestone_number:
        print("❌ Failed to create milestone")
        return
    
    # Create labels
    create_labels()
    
    # Import issues
    import_issues(milestone_number)
    
    print("\n" + "="*70)
    print("✅ GitHub Setup Complete!")
    print("="*70)
    print("\nNext steps:")
    print("  1. View issues: https://github.com/hellyparmar/R-DIOS/issues")
    print("  2. Assign issues to team members")
    print("  3. Create project board manually")
    print("  4. Send team notifications")

if __name__ == "__main__":
    main()

PYTHON_EOF

# Run the Python script
echo "Executing GitHub API setup..."
echo ""
python3 /tmp/github_setup.py

# Cleanup
rm /tmp/github_setup.py

echo ""
echo "Setup complete! Check the output above for status."
