#!/bin/bash
#============================================
# PHASE 0: GITHUB SETUP COMPLETION GUIDE
# Interactive Setup Instructions
#============================================

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                    GITHUB SETUP COMPLETION                        ║"
echo "║        Enterprise Retail Intelligence System - Phase 0             ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Authenticate with GitHub
echo "📝 STEP 1: Authenticate with GitHub"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "GitHub CLI is installed but needs authentication."
echo ""
echo "Run this command to authenticate:"
echo "  gh auth login"
echo ""
echo "When prompted:"
echo "  1. Choose: GitHub.com"
echo "  2. Choose: HTTPS"
echo "  3. Choose: Y (Authenticate with your GitHub credentials)"
echo "  4. Choose your preferred authentication method:"
echo "     - Paste token (if you have a Personal Access Token)"
echo "     - or use web browser to authenticate"
echo ""
echo "Required scopes: repo, read:org"
echo ""
read -p "Have you authenticated with GitHub? (yes/no): " auth_response

if [[ ! "$auth_response" =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Please run: gh auth login"
    exit 1
fi

echo "✅ Authentication verified!"
echo ""

# Step 2: Verify repository access
echo "📝 STEP 2: Verify Repository Access"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Testing GitHub access..."
gh repo view hellyparmar/R-DIOS --json name 2>/dev/null && echo "✅ Repository access confirmed!" || exit 1
echo ""

# Step 3: Create Milestone
echo "📝 STEP 3: Create GitHub Milestone"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Creating milestone: 'Phase 0 - Critical Blockers'"
echo ""

gh api -X POST repos/hellyparmar/R-DIOS/milestones \
  -f title="Phase 0 - Critical Blockers" \
  -f description="Database migration, configuration, pagination, and testing - Feb 17-20, 2026" \
  -f due_on="2026-02-20" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Milestone created!"
else
    echo "⚠️  Milestone may already exist (this is OK)"
fi
echo ""

# Step 4: Create Labels
echo "📝 STEP 4: Create GitHub Labels"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Creating 8 labels..."
echo ""

# Task labels
declare -a LABELS=(
    "task/database|0366d6|Database-related tasks"
    "task/config|0366d6|Configuration tasks"
    "task/pagination|0366d6|Pagination implementation"
    "task/testing|0366d6|Testing and QA"
    "task/deployment|0366d6|Deployment and gate approval"
    "priority/critical|d73a49|Blocks Phase 1"
    "priority/high|a2eeef|Important but not blocking"
    "status/in-progress|fbca04|Currently being worked on"
)

for label_def in "${LABELS[@]}"; do
    IFS='|' read -r name color description <<< "$label_def"
    echo "Creating: $name"
    gh api -X POST repos/hellyparmar/R-DIOS/labels \
      -f name="$name" \
      -f color="$color" \
      -f description="$description" 2>/dev/null || echo "  (Label may already exist)"
done

echo ""
echo "✅ Labels created!"
echo ""

# Step 5: Import GitHub Issues
echo "📝 STEP 5: Import GitHub Issues from Markdown Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

ISSUES_DIR="./PHASE_0_IMPLEMENTATION/github_issues"

if [ ! -d "$ISSUES_DIR" ]; then
    echo "❌ Issues directory not found: $ISSUES_DIR"
    exit 1
fi

echo "Found issues directory: $ISSUES_DIR"
echo ""
echo "Importing issues..."
echo ""

ISSUE_COUNT=0
for issue_file in "$ISSUES_DIR"/ISSUE_*.md; do
    if [ ! -f "$issue_file" ]; then
        continue
    fi

    ISSUE_COUNT=$((ISSUE_COUNT + 1))
    FILENAME=$(basename "$issue_file")
    
    # Extract title from filename
    TITLE="${FILENAME//ISSUE_/}"
    TITLE="${TITLE//.md/}"
    TITLE="${TITLE//_/ }"
    
    # Read content
    CONTENT=$(cat "$issue_file")
    
    echo "📌 Issue $ISSUE_COUNT: $TITLE"
    
    # Create issue with labels and milestone
    gh issue create \
        --title "$TITLE" \
        --body "$CONTENT" \
        --label "task/database,priority/critical" \
        --milestone "Phase 0 - Critical Blockers" \
        --repo hellyparmar/R-DIOS 2>/dev/null && echo "   ✅ Created" || echo "   ⚠️  May already exist"
done

echo ""
echo "✅ $ISSUE_COUNT issues imported!"
echo ""

# Step 6: Assign issues to team members
echo "📝 STEP 6: Assign Issues to Team Members (Manual)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Issue assignments:"
echo ""
echo "DevOps Lead:"
echo "  - Issue #1.1: PostgreSQL Infrastructure"
echo "  - Issue #5.2: Deployment Checklist"
echo ""
echo "Backend Lead:"
echo "  - Issue #1.2: PostgreSQL Schema"
echo "  - Issue #1.3: Data Migration"
echo "  - Issue #2.1: Backend Env Config"
echo "  - Issue #3.1: Pagination Backend"
echo ""
echo "Frontend Lead:"
echo "  - Issue #2.2: Frontend Env Config"
echo "  - Issue #3.2: Pagination Frontend"
echo ""
echo "QA Lead:"
echo "  - Issue #1.4: API Testing"
echo "  - Issue #4.1: Testing"
echo "  - Issue #4.2: Load Testing"
echo ""
echo "Product Lead:"
echo "  - Issue #5.1: Gate Approval"
echo ""
echo "⏳ Manual assignment via GitHub UI:"
echo "   1. Go to: github.com/hellyparmar/R-DIOS/issues"
echo "   2. Click each issue"
echo "   3. Assign to team member (right sidebar)"
echo ""

# Step 7: Create Project Board
echo "📝 STEP 7: Create GitHub Project Board (Manual)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⏳ Manual project board creation:"
echo ""
echo "Steps:"
echo "  1. Go to: github.com/hellyparmar/R-DIOS"
echo "  2. Click 'Projects' tab"
echo "  3. Click 'New Project' button"
echo "  4. Name: 'Phase 0 Execution (Feb 17-20)'"
echo "  5. Template: 'Table' or 'Board'"
echo "  6. Add these columns:"
echo "     - 📋 Backlog"
echo "     - 🔄 In Progress"
echo "     - ✅ Done"
echo "     - 🚫 Blocked"
echo ""
echo "  7. Add all imported issues to the project"
echo "  8. Set due date: Feb 20, 2026"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ GitHub Setup Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Authentication:     Complete"
echo "✅ Milestone:          Phase 0 - Critical Blockers (Due Feb 20)"
echo "✅ Labels:             8 labels created"
echo "✅ Issues:             $ISSUE_COUNT issues imported"
echo "⏳ Issue Assignments:   Pending (manual)"
echo "⏳ Project Board:       Pending (manual)"
echo ""
echo "Next Steps:"
echo "  1. ✅ Complete GitHub authentication"
echo "  2. ✅ Run this script to create milestone, labels, and import issues"
echo "  3. ⏳ Manually assign issues to team members"
echo "  4. ⏳ Create project board manually"
echo "  5. ⏳ Send team notifications with GitHub links"
echo ""
echo "Repository: https://github.com/hellyparmar/R-DIOS"
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
