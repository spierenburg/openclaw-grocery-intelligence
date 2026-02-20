#!/bin/bash
# OpenClaw Grocery Intelligence - Setup Script

set -e

echo "🛒 OPENCLAW GROCERY INTELLIGENCE SETUP"
echo "======================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi
echo "✅ Python 3 found"

# Check OpenClaw (optional)
if command -v openclaw &> /dev/null; then
    echo "✅ OpenClaw found"
else
    echo "⚠️  OpenClaw not found - install from https://openclaw.ai for full functionality"
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data
mkdir -p data/receipts
mkdir -p logs

# Create config from example
if [ ! -f "config/grocery-intelligence.json" ]; then
    if [ -f "config/grocery-intelligence.example.json" ]; then
        echo "⚙️  Creating configuration from example..."
        cp config/grocery-intelligence.example.json config/grocery-intelligence.json
        echo "✅ Configuration created - edit config/grocery-intelligence.json as needed"
    fi
else
    echo "✅ Configuration already exists"
fi

# Set script permissions
echo "🔧 Setting script permissions..."
chmod +x scripts/*.py

# Test basic functionality
echo "🧪 Testing system..."
if python3 scripts/grocery-intelligence-hub.py --help > /dev/null 2>&1; then
    echo "✅ Grocery intelligence hub working"
else
    echo "⚠️  Main script test failed - check dependencies"
fi

if python3 scripts/supermarket-prices.py --help > /dev/null 2>&1; then
    echo "✅ Price engine working"
else
    echo "⚠️  Price engine test failed"
fi

echo ""
echo "🎯 SETUP COMPLETE!"
echo ""
echo "📚 Next steps:"
echo "   1. Edit config/grocery-intelligence.json if needed"
echo "   2. Run: python3 scripts/grocery-intelligence-hub.py"
echo "   3. Try: python3 scripts/grocery-intelligence-hub.py price melk"
echo ""
echo "📖 Documentation: docs/GROCERY-SIMPLE-GUIDE.md"
echo "🔒 Privacy: All data stays local - see .gitignore"
echo ""
echo "Happy grocery shopping! 🛒💰"
