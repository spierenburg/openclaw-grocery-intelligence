# 🛒 Grocery Intelligence System - File & Data Flow Overview

> **📖 New to the system? Start with `GROCERY-SIMPLE-GUIDE.md` first!**
> 
> This document shows the technical details. For daily usage, just remember: `giq` does everything.

## 📂 File Structure (Grocery-Only)

```
~/.openclaw/workspace/
│
├── 🎯 CORE SCRIPTS (Daily Use)
│   ├── scripts/grocery-intelligence-hub.py    ← Main interface (90% of usage)
│   ├── scripts/supermarket-prices.py          ← Direct price queries  
│   ├── scripts/grocery-feedback.py            ← Feedback management
│   └── scripts/receipt-processor.py           ← Enhanced receipt processing
│
├── 📊 DATA STORAGE
│   ├── data/supermarkets-cache.json          ← 107K products database
│   ├── memory/grocery-feedback.jsonl         ← Your price feedback (12 entries)
│   └── expenses/receipts.jsonl               ← Receipt records with grocery intel
│
├── ⚙️ CONFIGURATION  
│   ├── config/grocery-intelligence.json      ← System settings
│   └── recipes/supermarkets.json             ← Store preferences
│
├── 📷 RECEIPT IMAGES
│   └── expenses/receipts/*.jpg                ← Receipt image files
│
├── 📋 DOCUMENTATION
│   ├── GROCERY-SIMPLE-GUIDE.md               ← **START HERE** - Simple usage guide
│   ├── GROCERY-SYSTEM-OVERVIEW.md            ← This file - system overview
│   ├── SYSTEM-CONSOLIDATION-SUMMARY.md       ← Before/after consolidation details
│   ├── GROCERY-INTELLIGENCE-PROJECT-STATUS.md ← Complete technical documentation
│   └── PRODUCTION-SUMMARY.md                 ← Production status
│
└── 🗄️ ARCHIVED COMPONENTS (Not Daily Use)
    └── scripts/archive/                       ← 9 archived scripts
        ├── grocery-only-receipt-scanner.py
        ├── production-grocery-intelligence.py
        └── ... (7 more setup/testing scripts)
```

## 🔄 Data Flow Diagram

```
📱 Signal Receipt Scan
         ↓
🤖 OCR Processing (receipt-processor.py)
         ↓
🔀 DUAL MODE DETECTION
    ├─ Regular Receipt ──→ Expense Tracking ──→ expenses/receipts.jsonl
    │                              └─→ Grocery Intelligence ──┐
    └─ "grocery scan" keyword ──→ Skip Expense Tracking ──────┘
                                                               ↓
📊 Price Analysis (grocery-intelligence-hub.py)
    ├─ Compare vs database (data/supermarkets-cache.json) ←──┘
    ├─ Generate feedback  
    └─ Store locally (memory/grocery-feedback.jsonl)
         ↓
📈 Results to User
    ├─ Signal message with price differences
    ├─ Command-line stats (gi-stats)
    └─ Interactive queries (giq)
```

## 💾 Where Your Data Actually Goes

### **INPUT DATA:**
```
📷 Receipt Images        → expenses/receipts/*.jpg
📱 Signal Messages       → Processed in real-time (not stored)
🛒 Shopping Data        → From checkjebon.nl daily (cached locally)
```

### **PROCESSED DATA:**
```
🧾 Receipt Records      → expenses/receipts.jsonl (with grocery intel)
💰 Expense Categories   → expenses/transactions.jsonl
🔍 Price Feedback       → memory/grocery-feedback.jsonl (local only)
📊 System Stats         → Real-time calculation (not stored)
```

### **EXTERNAL DATA:**
```
🌐 Product Database     → data/supermarkets-cache.json
    ├─ Source: checkjebon.nl (GitHub JSON)
    ├─ Size: 107,551 products from 12 stores
    ├─ Update: Daily at 06:00 via OpenClaw cron
    └─ Storage: Local cache (24h refresh)
```

## 🎯 What You Actually Need to Track

### **Daily Commands (Remember These):**
```bash
giq                     # Interactive mode (does everything)
gi-price melk          # Quick price check
gi-compare kipfilet    # Price comparison
gi-stats              # System status
```

### **Data Locations (Know These):**
```bash
📊 Price feedback:      memory/grocery-feedback.jsonl
🛒 Product database:    data/supermarkets-cache.json  
🧾 Receipt records:     expenses/receipts.jsonl
⚙️ System config:       config/grocery-intelligence.json
```

### **Key Scripts (Core 4 Only):**
```bash
grocery-intelligence-hub.py    # Main interface
supermarket-prices.py         # Price engine
grocery-feedback.py           # Feedback system
receipt-processor.py          # Receipt processing
```

## 🔍 System Status Check Commands

```bash
# Quick system overview
gi-stats

# Detailed component status
python3 scripts/grocery-feedback.py stats        # Feedback status
python3 scripts/supermarket-prices.py stats      # Database status  
ls -la data/supermarkets-cache.json             # Cache file info
wc -l memory/grocery-feedback.jsonl             # Feedback count
```

## 🛡️ Data Privacy & Control

### **What Stays Local:**
- ✅ All receipt images and OCR data
- ✅ Your grocery feedback and price analysis  
- ✅ Personal expense tracking records
- ✅ Shopping preferences and store priorities

### **What's External (Read-Only):**
- 📥 checkjebon.nl product database (public data)
- 📥 Daily price updates from GitHub API

### **No External Sharing:**
- ❌ No receipt data sent anywhere
- ❌ No grocery feedback uploaded  
- ❌ No personal shopping patterns shared
- ❌ Everything processes locally

## 🎯 Bottom Line: What You Need to Remember

**One Main Tool:**
```bash
giq    # Does everything you need
```

**Three Key Data Files:**
```bash
memory/grocery-feedback.jsonl     # Your price discoveries  
data/supermarkets-cache.json      # Product database (auto-updated)
expenses/receipts.jsonl           # Receipt records
```

**Daily Workflow:**
```
1. Scan receipt via Signal
2. Get automatic price feedback  
3. Use 'giq' for any grocery questions
4. System maintains itself automatically
```

**That's it!** Everything else is automated or archived. No need to track 15+ scripts when one main interface handles everything.