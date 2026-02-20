#!/bin/bash
# Initialize Git repository for OpenClaw Grocery Intelligence

echo "🚀 INITIALIZING GIT REPOSITORY"
echo "=============================="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi
echo "✅ Git found"

# Initialize repository
echo "📁 Initializing Git repository..."
git init

# Add all files
echo "📝 Adding files to Git..."
git add .

# Check what will be committed
echo "📊 Files to be committed:"
git status --porcelain

echo ""
echo "🛡️  Privacy check - these files are EXCLUDED by .gitignore:"
echo "   • data/grocery-feedback.jsonl (your personal feedback)"
echo "   • config/grocery-intelligence.json (your configuration)"  
echo "   • receipts/ and *.jpg files (receipt images)"
echo "   • memory/ and expenses/ (personal data)"

echo ""
read -p "👍 Ready to commit? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "💾 Creating initial commit..."
    git commit -m "Initial commit: OpenClaw Grocery Intelligence System

🛒 Features:
- Real-time price comparison across 12 Dutch supermarkets
- Automatic receipt analysis with price discrepancy detection  
- Privacy-first design with local-only data processing
- Interactive CLI with 107K+ product database
- Dual-mode operation for expense tracking + grocery intelligence

🔒 Privacy: All sensitive data excluded from repository"

    echo ""
    echo "✅ GIT REPOSITORY READY!"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Create repository on GitHub/GitLab:"
    echo "      - Go to https://github.com/new" 
    echo "      - Name: openclaw-grocery-intelligence"
    echo "      - Description: Privacy-first grocery price comparison system for OpenClaw"
    echo "      - Make it public for sharing!"
    echo ""
    echo "   2. Add remote and push:"
    echo "      git remote add origin <your-repo-url>"
    echo "      git branch -M main"
    echo "      git push -u origin main"
    echo ""
    echo "   3. Add topics/tags (GitHub):"
    echo "      - grocery"
    echo "      - price-comparison"  
    echo "      - openclaw"
    echo "      - receipt-analysis"
    echo "      - privacy-first"
    echo "      - dutch-supermarkets"
    echo ""
    echo "🎉 Ready to share with the world!"
    
else
    echo "⏸️  Skipped commit. Run 'git commit -m \"your message\"' when ready."
fi