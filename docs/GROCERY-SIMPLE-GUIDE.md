# 🛒 Grocery Intelligence - Simple Usage Guide

## 🎯 Just 4 Scripts You Need:

### 1. **grocery-intelligence-hub.py** - Main Interface
```bash
python3 scripts/grocery-intelligence-hub.py                # Interactive mode
python3 scripts/grocery-intelligence-hub.py price melk     # Quick price check
python3 scripts/grocery-intelligence-hub.py compare kaas   # Price comparison
python3 scripts/grocery-intelligence-hub.py stats          # System stats
```

### 2. **supermarket-prices.py** - Direct Price Queries  
```bash  
python3 scripts/supermarket-prices.py search melk          # Search products
python3 scripts/supermarket-prices.py compare kipfilet     # Compare prices
python3 scripts/supermarket-prices.py update               # Update database
```

### 3. **grocery-feedback.py** - Feedback Management
```bash
python3 scripts/grocery-feedback.py stats                  # Show feedback stats
python3 scripts/grocery-feedback.py verify receipt.jpg ah  # Manual feedback
```

### 4. **receipt-processor.py** - Enhanced Receipt Processing
```bash  
# This runs automatically when you scan receipts via Signal
# Now includes grocery intelligence for supported stores
```

## 🚀 Daily Usage:

**Most Common Commands:**
```bash
# Quick price check
gi-price melk                    # (alias, after terminal restart)
# OR
python3 scripts/grocery-intelligence-hub.py price melk

# Price comparison  
gi-compare kipfilet              # (alias)
# OR  
python3 scripts/grocery-intelligence-hub.py compare kipfilet

# Interactive mode (best for exploring)
giq                             # (alias)
# OR
python3 scripts/grocery-intelligence-hub.py
```

**Receipt Scanning:**
- Send receipt normally → Full expense tracking + grocery intelligence
- Send receipt + "grocery scan" → Grocery intelligence only (no expenses)

## 📊 Check System Status:
```bash
gi-stats                        # Quick stats
python3 scripts/grocery-feedback.py stats    # Detailed feedback stats
```

## 📊 Current System Status

**✅ PRODUCTION READY**
- **107,551 products** from 12 Dutch supermarkets in database
- **12 feedback entries** from real receipt analysis  
- **56 price discrepancies** detected and stored locally
- **Daily automated updates** at 06:00 via OpenClaw cron
- **Dual-mode receipt processing** (expense tracking + grocery-only)

## 📁 File Locations (Know These)

```bash
📊 Price feedback:      memory/grocery-feedback.jsonl
🛒 Product database:    data/supermarkets-cache.json (auto-updated daily)
🧾 Receipt records:     expenses/receipts.jsonl  
⚙️ System config:       config/grocery-intelligence.json
🗄️ Archived scripts:    scripts/archive/ (9 non-essential tools)
```

## 🔄 Data Flow Overview

```
📱 Signal Receipt Scan
    ↓ 
🤖 OCR Processing
    ↓
🔀 Mode Detection
    ├─ Regular → Expense Tracking + Grocery Intelligence
    └─ "grocery scan" → Grocery Intelligence Only
    ↓
🧠 Price Analysis (vs 107K product database)
    ↓
💾 Local Storage (memory/grocery-feedback.jsonl)
    ↓
📊 Results Display
```

## 🛡️ Privacy & Data Control

- ✅ **Everything stays local** - no external data sharing
- ✅ **Receipt data never uploaded** anywhere  
- ✅ **Your grocery intelligence** for your benefit only
- ✅ **Daily database updates** from public checkjebon.nl data
- ✅ **Full system control** - disable, reset, or export anytime

---

## 🎯 Bottom Line

**One command does everything:** `giq`

**System maintains itself automatically.**

**All your grocery data stays private and local.**

**Just scan receipts and get smarter about grocery shopping!** 🛒💰
