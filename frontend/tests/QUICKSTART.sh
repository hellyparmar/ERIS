#!/usr/bin/env bash
# Quick Start Script for Testing Frameworks
# Run this script to set up and execute tests

set -e

echo "============================================"
echo "Testing Framework - Quick Start"
echo "============================================"
echo ""

# Check if Node/npm installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install Node.js"
    exit 1
fi

echo "✅ npm found"
echo ""

# Check if Playwright installed
if ! npm list --depth=0 @playwright/test &> /dev/null; then
    echo "⚠️  Playwright not installed. Installing..."
    npm install --save-dev @playwright/test
fi

echo "✅ Playwright installed"
echo ""

# Install browsers if not present
echo "📦 Installing/updating Playwright browsers..."
npx playwright install

echo "✅ Browsers ready"
echo ""

# Check if dev server is running
echo "🔍 Checking development server..."
if curl -s http://127.0.0.1:4173 > /dev/null; then
    echo "✅ Dev server running at http://127.0.0.1:4173"
else
    echo ""
    echo "⚠️  Dev server not running!"
    echo ""
    echo "Start the development server in another terminal:"
    echo "  cd frontend"
    echo "  npm run dev"
    echo ""
    echo "Then come back and run this script again."
    echo ""
    exit 1
fi

echo ""
echo "============================================"
echo "Ready to Run Tests!"
echo "============================================"
echo ""
echo "Choose an option:"
echo ""
echo "1. Run all tests"
echo "   npx playwright test tests/"
echo ""
echo "2. Run Phase 2 (Responsive Design)"
echo "   npx playwright test tests/phase-2-responsive"
echo ""
echo "3. Run Phase 4 (Cross-Browser)"
echo "   npx playwright test tests/phase-4-cross-browser"
echo ""
echo "4. Run Phase 5 (Accessibility)"
echo "   npx playwright test tests/phase-5-accessibility"
echo ""
echo "5. Run tests with UI (interactive)"
echo "   npx playwright test tests/ --ui"
echo ""
echo "6. Run with visible browser"
echo "   npx playwright test tests/ --headed"
echo ""
echo "7. View test results"
echo "   npx playwright show-report"
echo ""
echo "============================================"
echo ""
echo "📖 Documentation:"
echo "  - Main guide: tests/TESTING_FRAMEWORK.md"
echo "  - Overview: tests/README.md"
echo "  - Phase 2: tests/phase-2-responsive/README.md"
echo "  - Phase 4: tests/phase-4-cross-browser/README.md"
echo "  - Phase 5: tests/phase-5-accessibility/README.md"
echo ""
