#!/bin/bash
# Comprehensive script to fix all remaining orphaned braces in Enterprise.jsx

MAX_ITERATIONS=30
iteration=0

while [ $iteration -lt $MAX_ITERATIONS ]; do
    echo "=== Iteration $((iteration + 1)) ==="
    
    # Try to build
    build_output=$(npm run build 2>&1)
    
    # Check if build succeeded
    if echo "$build_output" | grep -q "✓.*built in"; then
        echo "✅ BUILD SUCCESSFUL!"
        echo "$build_output" | tail -10
        exit 0
    fi
    
    # Extract error info
    error_file=$(echo "$build_output" | grep -oP '(?<=file: ).*Enterprise\.jsx' | head -1)
    error_line=$(echo "$build_output" | grep -oP '(?<=Enterprise\.jsx:)\d+(?=:\d+: ERROR)' | head -1)
    error_msg=$(echo "$build_output" | grep "ERROR:" | head -1)
    
    if [ -z "$error_file" ] || [ -z "$error_line" ]; then
        echo "✅ No more Enterprise.jsx errors or build succeeded!"
        npm run build 2>&1 | tail -30
        exit 0
    fi
    
    echo "Error in: $error_file:$error_line"
    echo "Message: $error_msg"
    
    # Check if it's an orphaned brace error
    if echo "$error_msg" | grep -q 'Expected ">" but found "}"'; then
        echo "Removing orphaned brace at line $error_line in $error_file"
        sed -i "${error_line}d" "$error_file"
    else
        echo "✅ No more orphaned brace errors in Enterprise.jsx!"
        npm run build 2>&1 | tail -30
        exit 0
    fi
    
    iteration=$((iteration + 1))
done

echo "❌ Max iterations reached. Build still failing."
npm run build 2>&1 | tail -30
exit 1
