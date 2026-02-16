#!/bin/bash
# Comprehensive script to remove all orphaned framer-motion props

echo "Fixing orphaned framer-motion props..."

# Find all JSX/JS files and remove orphaned closing braces after motion props
find src -name "*.jsx" -o -name "*.js" | while read file; do
    # Remove lines that are just "}" or "}" with whitespace after div/motion tags
    sed -i '/^[[:space:]]*}[[:space:]]*$/N;s/\n[[:space:]]*}[[:space:]]*$//g' "$file"
    
    # Remove orphaned animation props patterns
    sed -i '/initial={/,/^[[:space:]]*}[[:space:]]*$/d' "$file" 2>/dev/null || true
    sed -i '/animate={/,/^[[:space:]]*}[[:space:]]*$/d' "$file" 2>/dev/null || true
    sed -i '/variants={/,/^[[:space:]]*}[[:space:]]*$/d' "$file" 2>/dev/null || true
done

# Now run the original remove_framer_motion script
bash remove_framer_motion.sh

echo "Done!"
