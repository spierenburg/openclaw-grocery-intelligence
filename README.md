# 🛒 OpenClaw Grocery Intelligence System

A **privacy-first grocery price comparison and receipt analysis system** for OpenClaw with support for Dutch supermarkets.

## 🎯 Features

- **Real-time price comparison** across 12 Dutch supermarkets (107K+ products)
- **Automatic receipt analysis** with price discrepancy detection
- **Dual-mode processing**: Personal expense tracking + grocery-only intelligence  
- **Privacy-first design**: All data stays local, no external sharing
- **Interactive command-line interface** with simple aliases
- **Daily automated updates** from open grocery data sources

## 🚀 Quick Start

```bash
# 1. Set up the system
./setup.sh

# 2. Use interactive mode (main interface)
python3 scripts/grocery-intelligence-hub.py

# 3. Or use direct commands
python3 scripts/grocery-intelligence-hub.py price melk
python3 scripts/grocery-intelligence-hub.py compare kipfilet
```

## 📊 What It Does

### Price Intelligence
- Search products across **12 Dutch supermarkets** (AH, Lidl, Jumbo, Dirk, Hoogvliet, etc.)
- **Real-time price comparison** with cheapest-first sorting
- **Automatic daily updates** of 107K+ product database

### Receipt Analysis  
- **OCR processing** of grocery receipts
- **Price verification** against market database
- **Discrepancy detection** for significant price differences
- **Dual-mode operation**: expense tracking or intelligence-only

### Smart Shopping
- **Multi-store optimization**: Find best combination of stores for your list
- **Price trend analysis**: Historical price tracking and patterns
- **Intelligent product matching**: Fuzzy search with confidence scoring

## 🏪 Supported Stores

- **Albert Heijn** (16,173 products)
- **Jumbo** (17,739 products)  
- **Lidl** (19,170 products)
- **Plus** (16,129 products)
- **DekaMarkt** (10,728 products)
- **Dirk** (7,438 products)
- **Hoogvliet** (7,410 products)
- **Spar** (8,197 products)
- **Aldi** (1,738 products)
- **Poiesz** (1,904 products)
- **Vomar** (925 products)
- **Ekoplaza** (data pending)

## 🔒 Privacy & Security

- ✅ **All processing local** - no cloud dependencies
- ✅ **Receipt data never uploaded** anywhere
- ✅ **No personal data sharing** - everything stays on your machine
- ✅ **Open source grocery data** from checkjebon.nl public API
- ✅ **Full control** - disable, reset, or export your data anytime

## 📚 Documentation

- **[Simple Usage Guide](docs/GROCERY-SIMPLE-GUIDE.md)** ← **Start here** for daily usage
- **[System Overview](docs/GROCERY-SYSTEM-OVERVIEW.md)** ← Architecture and data flow
- **[Technical Documentation](docs/GROCERY-INTELLIGENCE-PROJECT-STATUS.md)** ← Complete technical details

## 🛠 Installation

### Requirements
- **OpenClaw** (https://openclaw.ai) 
- **Python 3.8+**
- **Ollama** (for local OCR processing)

### Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd openclaw-grocery-intelligence

# Run setup script
./setup.sh

# Copy example configuration
cp config/grocery-intelligence.example.json config/grocery-intelligence.json

# Test the system
python3 scripts/grocery-intelligence-hub.py stats
```

## 🎮 Usage Examples

### Interactive Mode (Recommended)
```bash
python3 scripts/grocery-intelligence-hub.py
# Provides full menu of options
```

### Direct Commands
```bash
# Price checking
python3 scripts/grocery-intelligence-hub.py price "halfvolle melk"
python3 scripts/grocery-intelligence-hub.py compare "kipfilet"

# System status
python3 scripts/grocery-intelligence-hub.py stats

# Feedback management
python3 scripts/grocery-feedback.py stats
```

### Receipt Processing
Send receipt images via OpenClaw Signal integration:
- **Normal receipt** → Full expense tracking + grocery intelligence
- **Receipt + "grocery scan"** → Price analysis only (no expense tracking)

## 🏗 Architecture

```
📱 Receipt Scan (Signal/OpenClaw)
    ↓
🤖 OCR Processing (Local Ollama)
    ↓  
🔀 Mode Detection (Expense tracking vs grocery-only)
    ↓
🧠 Price Analysis (vs 107K product database)
    ↓
💾 Local Storage (JSONL format)
    ↓
📊 Results & Insights
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Setup
```bash
# Clone for development
git clone <your-repo-url>
cd openclaw-grocery-intelligence

# Install dependencies
pip install -r requirements.txt

# Run tests
python3 -m pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[checkjebon.nl](https://checkjebon.nl)** - Open grocery price data
- **[OpenClaw](https://openclaw.ai)** - AI assistant platform
- **Dutch Supermarket Chains** - For providing online product catalogs

## 🔗 Related Projects

- **[checkjebon-js](https://github.com/supermarkt/checkjebon-js)** - JavaScript library for grocery price data
- **[OpenClaw](https://github.com/openclaw/openclaw)** - AI assistant platform

---

**Built with ❤️ for smarter grocery shopping in the Netherlands** 🇳🇱

*Saving money, one receipt at a time!* 💰🛒
