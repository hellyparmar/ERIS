#!/bin/bash
#============================================
# QUICK START: GitHub Setup for Phase 0
#============================================

cat << 'EOF'

╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                    PHASE 0 GITHUB SETUP - QUICK START                    ║
║                                                                           ║
║             Personal Access Token Required (2 minutes to get)             ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

📋 INSTRUCTIONS
═══════════════════════════════════════════════════════════════════════════

STEP 1: Get Your GitHub Token
────────────────────────────────────────────────────────────────────────

1. Open this link in your browser:
   👉 https://github.com/settings/tokens

2. Click: "Generate new token (classic)"

3. Fill in:
   Name: Phase 0 Setup Token
   
4. Select scopes (checkboxes):
   ☑ repo (all permissions)
   ☑ read:org

5. Click: "Generate token"

6. COPY the token (you won't see it again!)
   It looks like: ghp_xxxxxxxxxxxxxxxxxxxx

═══════════════════════════════════════════════════════════════════════════

STEP 2: Paste Token Below
────────────────────────────────────────────────────────────────────────

EOF

read -sp "Paste your GitHub token here: " GITHUB_TOKEN
echo ""
echo ""

# Validate token format
if [[ ! "$GITHUB_TOKEN" =~ ^ghp_ ]]; then
    echo "❌ Invalid token format (should start with 'ghp_')"
    exit 1
fi

# Verify token works
echo "🔍 Verifying token..."
VERIFY=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | grep '"login"' || echo "")

if [ -z "$VERIFY" ]; then
    echo "❌ Token verification failed"
    echo "   Make sure you have the correct token"
    exit 1
fi

echo "✅ Token verified!"
echo ""

# Export token and run setup
export GITHUB_TOKEN="$GITHUB_TOKEN"
cd /home/petpooja/Enterprise\ Retail\ Intelligence\ System

echo "🚀 Running GitHub setup..."
echo ""

./PHASE_0_IMPLEMENTATION/GITHUB_SETUP_PYTHON.sh

# Check if setup was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════════════╗"
    echo "║                      ✅ SETUP COMPLETE!                                   ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Next Steps:"
    echo ""
    echo "1. ⏳ MANUAL: Assign issues to team members"
    echo "   Go to: https://github.com/hellyparmar/R-DIOS/issues"
    echo "   See GITHUB_SETUP_GUIDE.md for assignments"
    echo ""
    echo "2. ⏳ MANUAL: Create project board"
    echo "   Go to: https://github.com/hellyparmar/R-DIOS"
    echo "   Click 'Projects' → 'New project'"
    echo "   Name: 'Phase 0 Execution (Feb 17-20)'"
    echo ""
    echo "3. ✅ Send team notifications"
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo ""
else
    echo "❌ Setup failed - check the output above"
    exit 1
fi
