#!/bin/bash
# Batch fix hardcoded localhost URLs in frontend files
# R-DIOS Phase 0 - Task 2

set -e

echo "============================================================"
echo "Fixing Hardcoded localhost URLs"
echo "============================================================"

# Files to fix (excluding api.js, useApi.js, Dashboard.jsx, Forecasts.jsx, Analytics.jsx - already fixed)
FILES=(
    "src/pages/AIAssistant.jsx"
    "src/pages/POS.jsx"
    "src/pages/Loyalty.jsx"
    "src/pages/Inventory.jsx"
    "src/pages/Alerts.jsx"
    "src/pages/Enterprise.jsx"
    "src/pages/Invoices.jsx"
    "src/components/layout/FloatingAIAssistant.jsx"
    "src/components/ui/ExportButton.jsx"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "Processing: $file"
        # Replace hardcoded URLs with ${API_BASE}
        sed -i "s|'http://localhost:8000|\`\${API_BASE}|g" "$file"
        sed -i "s|\"http://localhost:8000|\`\${API_BASE}|g" "$file"
        sed -i "s|8000/api|\${API_BASE}/api|g" "$file"
        echo "  ✓ Fixed"
    else
        echo "  ⚠ File not found: $file"
    fi
done

echo ""
echo "============================================================"
echo "Verifying fixes..."
echo "============================================================"
remaining=$(grep -r "http://localhost:8000" src/ --include="*.js" --include="*.jsx" -l 2>/dev/null | grep -v "api.js" | grep -v "useApi.js" | wc -l)
echo "Remaining files with hardcoded URLs: $remaining"

if [ "$remaining" -eq 0 ]; then
    echo "✓ All hardcoded URLs fixed!"
else
    echo "⚠ Some files still have hardcoded URLs:"
    grep -r "http://localhost:8000" src/ --include="*.js" --include="*.jsx" -l | grep -v "api.js" | grep -v "useApi.js"
fi
