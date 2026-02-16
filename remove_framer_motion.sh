#!/bin/bash
# Script to remove Framer Motion from R-DIOS frontend
# Phase 0 - Task 4

set -e

echo "============================================================"
echo "Framer Motion Removal Script"
echo "============================================================"
echo ""

# Find all files with framer-motion imports
FILES=$(grep -rl "from 'framer-motion'" src/ --include="*.jsx" --include="*.js" 2>/dev/null || true)

if [ -z "$FILES" ]; then
    echo "✓ No framer-motion imports found!"
    exit 0
fi

echo "Found framer-motion in the following files:"
echo "$FILES" | while read file; do
    echo "  • $file"
done
echo ""

FILE_COUNT=$(echo "$FILES" | wc -l)
echo "Total files to process: $FILE_COUNT"
echo ""

# Backup
BACKUP_DIR="framer_motion_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "Creating backup in: $BACKUP_DIR"
echo "$FILES" | while read file; do
    mkdir -p "$BACKUP_DIR/$(dirname "$file")"
    cp "$file" "$BACKUP_DIR/$file"
done
echo "✓ Backup complete"
echo ""

# Process each file
echo "Processing files..."
echo ""

PROCESSED=0
echo "$FILES" | while read file; do
    echo "Processing: $file"
    
    # Create temp file
    TEMP_FILE="${file}.tmp"
    
    # Remove framer-motion import lines
    sed '/^import.*framer-motion/d' "$file" > "$TEMP_FILE"
    
    # Replace motion.div with div
    sed -i 's/<motion\.div/<div/g' "$TEMP_FILE"
    sed -i 's/<\/motion\.div>/<\/div>/g' "$TEMP_FILE"
    
    # Replace motion.button with button
    sed -i 's/<motion\.button/<button/g' "$TEMP_FILE"
    sed -i 's/<\/motion\.button>/<\/button>/g' "$TEMP_FILE"
    
    # Replace motion.span with span
    sed -i 's/<motion\.span/<span/g' "$TEMP_FILE"
    sed -i 's/<\/motion\.span>/<\/span>/g' "$TEMP_FILE"
    
    # Replace motion.p with p
    sed -i 's/<motion\.p/<p/g' "$TEMP_FILE"
    sed -i 's/<\/motion\.p>/<\/p>/g' "$TEMP_FILE"
    
    # Replace motion.h1, h2, h3 with regular headers
    sed -i 's/<motion\.h1/<h1/g' "$TEMP_FILE"
    sed -i 's/<\/motion\.h1>/<\/h1>/g' "$TEMP_FILE"
    sed -i 's/<motion\.h2/<h2/g' "$TEMP_FILE"
    sed -i 's/<\/motion\.h2>/<\/h2>/g' "$TEMP_FILE"
    sed -i 's/<motion\.h3/<h3/g' "$TEMP_FILE"
    sed -i 's/<\/motion\.h3>/<\/h3>/g' "$TEMP_FILE"
    
    # Remove AnimatePresence wrapper (keep children)
    sed -i 's/<AnimatePresence[^>]*>//g' "$TEMP_FILE"
    sed -i 's/<\/AnimatePresence>//g' "$TEMP_FILE"
    
    # Remove common framer-motion props (initial, animate, exit, whileHover, whileTap, variants, transition)
    sed -i 's/initial={[^}]*}//g' "$TEMP_FILE"
    sed -i 's/animate={[^}]*}//g' "$TEMP_FILE"
    sed -i 's/exit={[^}]*}//g' "$TEMP_FILE"
    sed -i 's/whileHover={[^}]*}//g' "$TEMP_FILE"
    sed -i 's/whileTap={[^}]*}//g' "$TEMP_FILE"
    sed -i 's/variants={[^}]*}//g' "$TEMP_FILE"
    sed -i 's/transition={[^}]*}//g' "$TEMP_FILE"
    
    # Move temp file to original
    mv "$TEMP_FILE" "$file"
    
    echo "  ✓ Processed"
    PROCESSED=$((PROCESSED + 1))
done

echo ""
echo "============================================================"
echo "Processing Complete"
echo "============================================================"
echo "Files processed: $FILE_COUNT"
echo "Backup location: $BACKUP_DIR"
echo ""
echo "Next steps:"
echo "1. Review changes with: git diff"
echo "2. Remove framer-motion from package.json"
echo "3. Run: npm install"
echo "4. Test the application"
echo ""
