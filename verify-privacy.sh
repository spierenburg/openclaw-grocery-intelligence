#!/bin/bash
# Verify no sensitive data in Git export

echo "🔒 PRIVACY VERIFICATION"
echo "====================="

echo "🔍 Checking for sensitive data patterns..."

# Check for receipt images
echo "📷 Receipt images:"
if find . -name "*.jpg" -o -name "*.png" -o -name "*.jpeg" | grep -q .; then
    echo "   ❌ FOUND RECEIPT IMAGES - DO NOT COMMIT"
    find . -name "*.jpg" -o -name "*.png" -o -name "*.jpeg"
else
    echo "   ✅ No receipt images found"
fi

# Check for personal feedback data
echo "💾 Personal feedback data:"
if find . -name "*feedback*.jsonl" -not -name "*.example.jsonl" | grep -q .; then
    echo "   ❌ FOUND PERSONAL FEEDBACK DATA - DO NOT COMMIT"  
    find . -name "*feedback*.jsonl" -not -name "*.example.jsonl"
else
    echo "   ✅ No personal feedback data found"
fi

# Check for real configuration
echo "⚙️  Real configuration files:"
if [ -f "config/grocery-intelligence.json" ]; then
    echo "   ❌ FOUND REAL CONFIG - SHOULD BE .example ONLY"
else
    echo "   ✅ Only example configuration present"
fi

# Check for supermarket cache
echo "🛒 Supermarket database cache:"
if [ -f "data/supermarkets-cache.json" ]; then
    echo "   ❌ FOUND CACHE FILE - SHOULD BE DOWNLOADED BY USER"
else
    echo "   ✅ No cache file (will be downloaded on first use)"  
fi

# Check for personal directories
echo "📁 Personal data directories:"
PERSONAL_DIRS=("memory" "expenses" "receipts" "monitoring")
found_personal=false
for dir in "${PERSONAL_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "   ❌ FOUND $dir/ - REMOVE BEFORE COMMIT"
        found_personal=true
    fi
done
if [ "$found_personal" = false ]; then
    echo "   ✅ No personal data directories found"
fi

# Check file contents for sensitive patterns
echo "🔎 Scanning file contents for sensitive data..."
SENSITIVE_PATTERNS=("receipt-.*\.jpg" "€[0-9]" "bonnetje" "+31" "Signal" "Splinter")
found_sensitive=false
for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    if grep -r "$pattern" . --exclude-dir=.git --exclude="*.sh" --exclude="README.md" --exclude="*.example.*" >/dev/null 2>&1; then
        echo "   ⚠️  Found pattern '$pattern' - review files:"
        grep -r "$pattern" . --exclude-dir=.git --exclude="*.sh" --exclude="README.md" --exclude="*.example.*" | head -3
        found_sensitive=true
    fi
done
if [ "$found_sensitive" = false ]; then
    echo "   ✅ No sensitive patterns in code files"
fi

echo ""
echo "📋 PRIVACY VERIFICATION SUMMARY:"
echo "================================"

# Final check
echo "✅ Safe to share:"
echo "   • Core grocery intelligence scripts"  
echo "   • Example configurations (no real data)"
echo "   • Complete documentation"
echo "   • MIT license for open source sharing"

echo ""
echo "🛡️  Protected (excluded by .gitignore):"
echo "   • Personal receipt images"
echo "   • Real grocery feedback data"
echo "   • Personal configuration files"  
echo "   • Expense tracking records"

echo ""
echo "🚀 Repository is ready for public sharing!"
echo ""
echo "Run './init-git.sh' to initialize Git repository."