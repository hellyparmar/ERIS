#!/bin/bash
# Comprehensive cleanup of leftover framer-motion props

echo "Cleaning up leftover framer-motion animation props..."

# Find all JSX files and remove orphaned animation props
find src/ -name "*.jsx" -type f | while read file; do
    # Remove lines that are just "}" or whitespace + "}"
    # But only if they appear between JSX tags in suspicious patterns
    
    # Use perl for more sophisticated pattern matching
    perl -i -pe 's/^\s*}\s*$//g if /key=/ .. /<\/div>/' "$file" 2>/dev/null || true
done

echo "✓ Cleanup complete"
