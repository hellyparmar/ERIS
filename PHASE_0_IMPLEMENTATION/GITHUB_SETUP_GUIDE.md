# GitHub Setup Guide - Phase 0 Implementation

## Quick Start: Complete GitHub Setup in 2 Steps

### Step 1: Get Your GitHub Personal Access Token

**Option A: Create a New Token (Recommended)**

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: `Phase 0 Setup Token`
4. Select these scopes:
   - ✅ repo (all permissions)
   - ✅ read:org
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

**Option B: Use Existing Token**
- If you already have a GitHub CLI token, you can reuse it

---

### Step 2: Run GitHub Setup

#### Using Python API (Recommended - No interaction needed)

```bash
cd /home/petpooja/Enterprise\ Retail\ Intelligence\ System

# Set your token and run the automated setup
export GITHUB_TOKEN='ghp_YOUR_TOKEN_HERE'
./PHASE_0_IMPLEMENTATION/GITHUB_SETUP_PYTHON.sh
```

**What it does:**
- ✅ Creates milestone: "Phase 0 - Critical Blockers" (due Feb 20)
- ✅ Creates 8 labels (task, priority, status labels)
- ✅ Imports 12 GitHub issues
- ✅ Assigns all issues to milestone
- ✅ Sets initial labels on issues

**Expected Output:**
```
✅ Milestone created (ID: 1)
✅ Labels setup complete (8 created/updated)
✅ Issues import complete (12 imported)
✅ GitHub Setup Complete!
```

**Time needed:** 2-3 minutes

---

#### Using GitHub CLI (Interactive)

If you prefer using GitHub CLI directly:

```bash
# Authenticate with GitHub
gh auth login

# Choose:
# - GitHub.com
# - HTTPS
# - Authenticate with your credentials
# - Paste your token or use browser

# Run setup script
./PHASE_0_IMPLEMENTATION/GITHUB_SETUP_INTERACTIVE.sh
```

---

## Complete Checklist

After running the setup scripts, verify:

- [ ] **Milestone Created**
  - Go to: https://github.com/hellyparmar/R-DIOS/milestones
  - Should see: "Phase 0 - Critical Blockers" (Due Feb 20)

- [ ] **Labels Created** (8 total)
  - Go to: https://github.com/hellyparmar/R-DIOS/labels
  - Should see:
    - task/database
    - task/config
    - task/pagination
    - task/testing
    - task/deployment
    - priority/critical
    - priority/high
    - status/in-progress

- [ ] **Issues Imported** (12 total)
  - Go to: https://github.com/hellyparmar/R-DIOS/issues
  - Should see 12 issues with Phase 0 milestone assigned:
    1. PostgreSQL Infrastructure
    2. PostgreSQL Schema
    3. Data Migration
    4. API Testing
    5. Backend Env Config
    6. Frontend Env Config
    7. Pagination Backend
    8. Pagination Frontend
    9. Testing
    10. Load Testing
    11. Gate Approval
    12. Deployment Checklist

---

## Manual Tasks (After Script Runs)

### Assign Issues to Team Members

Issues are created but need manual assignment:

1. Go to: https://github.com/hellyparmar/R-DIOS/issues
2. For each issue, click it and assign to the responsible team member:

**DevOps Lead:**
- #1: PostgreSQL Infrastructure
- #12: Deployment Checklist

**Backend Lead:**
- #2: PostgreSQL Schema
- #3: Data Migration
- #5: Backend Env Config
- #7: Pagination Backend

**Frontend Lead:**
- #6: Frontend Env Config
- #8: Pagination Frontend

**QA Lead:**
- #4: API Testing
- #9: Testing
- #10: Load Testing

**Product Lead:**
- #11: Gate Approval

### Create Project Board

1. Go to: https://github.com/hellyparmar/R-DIOS
2. Click "Projects" tab
3. Click "New project"
4. Configure:
   - Name: `Phase 0 Execution (Feb 17-20)`
   - Template: `Table` or `Board`
   - Add columns:
     - 📋 Backlog
     - 🔄 In Progress
     - ✅ Done
     - 🚫 Blocked
5. Add all 12 issues to the project
6. Set due date: Feb 20, 2026

---

## Troubleshooting

### Error: "GITHUB_TOKEN not set"

**Solution:**
```bash
export GITHUB_TOKEN='your_token_here'
./PHASE_0_IMPLEMENTATION/GITHUB_SETUP_PYTHON.sh
```

### Error: "Authentication failed"

**Solution:**
- Verify your token is correct (copy from GitHub settings)
- Ensure token has `repo` and `read:org` scopes
- Check token isn't expired

### Error: "gh: command not found"

**Solution:**
```bash
sudo apt-get install gh
```

### Issues show as "already exists"

**This is OK!** Means:
- Milestone was already created
- Labels were already created
- Some issues were already imported

Just verify they exist and have correct properties.

---

## Next Steps After GitHub Setup

1. ✅ Create GitHub milestone
2. ✅ Create GitHub labels
3. ✅ Import GitHub issues
4. ⏳ **Assign issues to team members** (manual)
5. ⏳ **Create project board** (manual)
6. ⏳ **Send team notifications with issue links**
7. ⏳ **Final verification** (Sunday Feb 16)

---

## Commands Reference

```bash
# Check if token is set
echo $GITHUB_TOKEN

# Set token (replace with your actual token)
export GITHUB_TOKEN='ghp_YOUR_TOKEN_HERE'

# Run Python API setup
./PHASE_0_IMPLEMENTATION/GITHUB_SETUP_PYTHON.sh

# View issues
gh issue list --repo hellyparmar/R-DIOS

# View milestone
gh milestone list --repo hellyparmar/R-DIOS

# View labels
gh label list --repo hellyparmar/R-DIOS
```

---

## Security Notes

- ⚠️ **Never commit your token to Git!**
- ⚠️ **Never share your token in messages or documents**
- ⚠️ **Token is only valid during your session**
- ✅ Use environment variable (not in scripts)
- ✅ Regenerate token if it's compromised
- ✅ Delete token when setup is complete

---

## Document Reference

**Setup Scripts:**
- `GITHUB_SETUP_INTERACTIVE.sh` - Interactive gh CLI approach
- `GITHUB_SETUP_PYTHON.sh` - Automated Python API approach (recommended)

**Related Documentation:**
- `PHASE_0_SETUP.md` - Original setup instructions
- `PHASE_0_PRE_EXECUTION_SETUP.md` - Complete execution guide
- `PHASE_0_EXECUTION_CHECKLIST.txt` - Pre-kickoff verification

---

**Status:** Ready for Phase 0 Execution (Feb 17, 2026)
**Last Updated:** Feb 15, 2026
