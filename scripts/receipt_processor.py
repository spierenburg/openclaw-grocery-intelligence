#!/usr/bin/env python3
"""
Receipt Processor for OpenClaw
Finds and processes receipt images from Signal/OpenClaw inbound media.
Uses local Ollama vision model for privacy-first OCR.
"""

import base64
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path


# Grocery Intelligence Integration
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("grocery_feedback", Path(__file__).parent / "grocery_feedback.py")
    grocery_feedback = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(grocery_feedback)
    GROCERY_INTELLIGENCE_AVAILABLE = True
except Exception as e:
    print(f"⚠️  Grocery intelligence not available: {e}")
    GROCERY_INTELLIGENCE_AVAILABLE = False

STORE_MAPPING = {
    'albert heijn': 'ah', 'ah': 'ah', 'lidl': 'lidl', 'jumbo': 'jumbo',
    'dirk': 'dirk', 'dirk van den broek': 'dirk', 'hoogvliet': 'hoogvliet',
    'aldi': 'aldi', 'plus': 'plus'
}

# Paths
INBOUND_DIR = Path.home() / ".openclaw" / "media" / "inbound"
RECEIPTS_DIR = Path.home() / ".openclaw" / "workspace" / "expenses" / "receipts"
RECEIPTS_JSONL = Path.home() / ".openclaw" / "workspace" / "expenses" / "receipts.jsonl"

# Ensure directories exist
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
RECEIPTS_JSONL.parent.mkdir(parents=True, exist_ok=True)


def find_recent_image(max_age_seconds: int = 300) -> dict | None:
    """Find the most recent image in the inbound folder."""
    now = datetime.now().timestamp()
    candidates = []
    
    for f in INBOUND_DIR.iterdir():
        if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
            mtime = f.stat().st_mtime
            age = now - mtime
            if age <= max_age_seconds:
                candidates.append({
                    "path": str(f),
                    "filename": f.name,
                    "age_seconds": int(age),
                    "mtime": mtime
                })
    
    if not candidates:
        return None
    
    # Return most recent
    candidates.sort(key=lambda x: x["mtime"], reverse=True)
    return candidates[0]


def run_tesseract(image_path: str) -> str:
    """Run Tesseract OCR on an image."""
    result = subprocess.run(
        ["/opt/homebrew/bin/tesseract", image_path, "stdout", "-l", "nld+eng"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


# Ollama config
OLLAMA_URL = "http://10.252.1.142:11434/api/generate"
VISION_MODEL = "llama3.2-vision:11b"


def analyze_with_ollama(image_path: str) -> dict:
    """Analyze receipt image using local Ollama vision model."""
    import re
    
    # Read and encode image
    with open(image_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")
    
    prompt = """Look at this receipt image. Extract the purchased items - these are lines with a quantity (Hvl/Aantal), product name, and price. 
IGNORE: BTW details, loyalty cards, totals, payment info, store info.

Return ONLY valid JSON:
{"is_receipt":true,"store":"StoreName","date":"YYYY-MM-DD","time":"HH:MM","amount":0.00,"items":["Product Name 1","Product Name 2"],"category":"klussen"}

Categories: boodschappen (groceries), horeca (restaurant/cafe), transport (fuel/parking), klussen (hardware/DIY), wonen (home), kleding (clothes), elektronica (electronics), gezondheid (pharmacy), overig (other)

For Praxis/Gamma/Hornbach use "klussen". For AH/Jumbo/Lidl use "boodschappen".

If not a receipt: {"is_receipt":false}"""

    payload = {
        "model": VISION_MODEL,
        "prompt": prompt,
        "images": [img_base64],
        "stream": False,
        "options": {"temperature": 0.1}
    }
    
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            response_text = result.get("response", "")
            
            # Try to extract JSON from response
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # Fallback: parse structured text response
            parsed = {"is_receipt": True, "raw": response_text}
            
            # Extract store
            store_match = re.search(r'\*\*Store\*\*[:\s]+([^\n*]+)', response_text, re.I)
            if store_match:
                parsed["store"] = store_match.group(1).strip()
            
            # Extract date
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', response_text)
            if date_match:
                parsed["date"] = date_match.group(1)
            
            # Extract time
            time_match = re.search(r'\*\*Time\*\*[:\s]+(\d{1,2}:\d{2})', response_text, re.I)
            if time_match:
                parsed["time"] = time_match.group(1)
            
            # Extract amount
            amount_match = re.search(r'\*\*Amount\*\*[:\s]+[€]?(\d+[.,]\d{2})', response_text, re.I)
            if not amount_match:
                amount_match = re.search(r'(\d+[.,]\d{2})', response_text)
            if amount_match:
                parsed["amount"] = float(amount_match.group(1).replace(",", "."))
            
            return parsed
            
    except Exception as e:
        return {"error": str(e)}


def save_receipt(receipt_data: dict, image_path: str) -> dict:
    """
    Save receipt to JSONL and copy image to receipts folder.
    
    Args:
        receipt_data: Dict with keys like store, date, amount, items, category
        image_path: Path to the original image
    
    Returns:
        Dict with saved file info
    """
    src = Path(image_path)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    new_filename = f"receipt-{timestamp}{src.suffix}"
    dest_path = RECEIPTS_DIR / new_filename
    
    # Copy image
    shutil.copy2(src, dest_path)
    
    # Build record
    record = {
        **receipt_data,
        "image_file": new_filename,
        "original_file": src.name,
        "processed_at": datetime.now().isoformat()
    }
    
    # Append to JSONL
    with open(RECEIPTS_JSONL, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    return {
        "saved": True,
        "image_file": str(dest_path),
        "record": record
    }


def cmd_find(args):
    """Find recent images."""
    max_age = int(args[0]) if args else 300
    result = find_recent_image(max_age)
    if result:
        print(json.dumps({"status": "found", **result}, indent=2))
    else:
        print(json.dumps({"status": "not_found", "max_age_seconds": max_age}))
        sys.exit(1)


def cmd_analyze(args):
    """Analyze image with Ollama vision model."""
    if not args:
        # Find most recent
        result = find_recent_image(3600)
        if not result:
            print(json.dumps({"error": "No recent image found"}))
            sys.exit(1)
        image_path = result["path"]
    else:
        image_path = args[0]
    
    print(f"Analyzing {image_path} with {VISION_MODEL}...", file=sys.stderr)
    analysis = analyze_with_ollama(image_path)
    analysis["image_path"] = image_path
    print(json.dumps(analysis, indent=2))


def cmd_ocr(args):
    """Run OCR on an image."""
    if not args:
        # Find most recent
        result = find_recent_image(3600)
        if not result:
            print(json.dumps({"error": "No recent image found"}))
            sys.exit(1)
        image_path = result["path"]
    else:
        image_path = args[0]
    
    text = run_tesseract(image_path)
    print(json.dumps({
        "image": image_path,
        "ocr_text": text,
        "lines": len(text.split("\n")) if text else 0
    }, indent=2))


def cmd_save(args):
    """Save a receipt. Expects JSON as first arg or stdin."""
    if args:
        data = json.loads(args[0])
        image_path = args[1] if len(args) > 1 else None
    else:
        data = json.load(sys.stdin)
        image_path = None
    
    if not image_path:
        # Find most recent image
        result = find_recent_image(3600)
        if not result:
            print(json.dumps({"error": "No image path provided and no recent image found"}))
            sys.exit(1)
        image_path = result["path"]
    
    saved = save_receipt(data, image_path)
    print(json.dumps(saved, indent=2))


def cmd_list(args):
    """List saved receipts."""
    limit = int(args[0]) if args else 10
    
    if not RECEIPTS_JSONL.exists():
        print(json.dumps({"receipts": [], "total": 0}))
        return
    
    receipts = []
    with open(RECEIPTS_JSONL) as f:
        for line in f:
            line = line.strip()
            if line:
                receipts.append(json.loads(line))
    
    # Most recent first
    receipts.reverse()
    
    print(json.dumps({
        "receipts": receipts[:limit],
        "total": len(receipts)
    }, indent=2))


def cmd_stats(args):
    """Get receipt statistics."""
    if not RECEIPTS_JSONL.exists():
        print(json.dumps({"total": 0, "total_amount": 0}))
        return
    
    receipts = []
    with open(RECEIPTS_JSONL) as f:
        for line in f:
            line = line.strip()
            if line:
                receipts.append(json.loads(line))
    
    total_amount = 0
    by_store = {}
    by_category = {}
    
    for r in receipts:
        amount = r.get("amount", 0)
        if isinstance(amount, str):
            # Parse "€12.50" format
            amount = float(amount.replace("€", "").replace(",", ".").strip())
        total_amount += amount
        
        store = r.get("store", "Unknown")
        by_store[store] = by_store.get(store, 0) + amount
        
        category = r.get("category", "Uncategorized")
        by_category[category] = by_category.get(category, 0) + amount
    
    print(json.dumps({
        "total_receipts": len(receipts),
        "total_amount": round(total_amount, 2),
        "by_store": {k: round(v, 2) for k, v in sorted(by_store.items(), key=lambda x: -x[1])},
        "by_category": {k: round(v, 2) for k, v in sorted(by_category.items(), key=lambda x: -x[1])}
    }, indent=2))


def cmd_cleanup(args):
    """Remove receipt images older than N days (default 30). Keeps JSONL data."""
    max_days = int(args[0]) if args else 30
    now = datetime.now().timestamp()
    max_age = max_days * 24 * 60 * 60
    
    removed = []
    kept = []
    
    for f in RECEIPTS_DIR.iterdir():
        if f.suffix.lower() in ('.jpg', '.jpeg', '.png'):
            age = now - f.stat().st_mtime
            if age > max_age:
                f.unlink()
                removed.append(f.name)
            else:
                kept.append(f.name)
    
    print(json.dumps({
        "removed": len(removed),
        "kept": len(kept),
        "max_days": max_days,
        "removed_files": removed
    }, indent=2))



def generate_grocery_intelligence(receipt_data):
    """Generate grocery intelligence feedback from receipt data."""
    if not GROCERY_INTELLIGENCE_AVAILABLE:
        return
    
    store_name = receipt_data.get('store', '').lower()
    if store_name not in STORE_MAPPING:
        return  # Not a grocery store
    
    mapped_store = STORE_MAPPING[store_name]
    items = receipt_data.get('items', [])
    
    # Extract items with prices
    feedback_items = []
    for item in items:
        if isinstance(item, dict) and 'name' in item and 'price' in item:
            try:
                price = float(item['price'])
                if price > 0:
                    feedback_items.append({
                        'name': item['name'],
                        'price': price,
                        'date': receipt_data.get('date', '2026-02-20')
                    })
            except (ValueError, TypeError):
                continue
    
    if feedback_items:
        try:
            discrepancies = grocery_feedback.verify_receipt_against_checkjebon(feedback_items, mapped_store)
            if discrepancies:
                grocery_feedback.submit_feedback_locally(discrepancies)
                significant = [d for d in discrepancies if abs(d['price_difference']) > 0.20]
                if significant:
                    print(f"🧠 Grocery Intelligence: Found {len(significant)} significant price differences")
                    for d in significant[:2]:
                        direction = "higher" if d['price_difference'] > 0 else "lower"
                        print(f"   • {d['receipt_product']}: €{abs(d['price_difference']):.2f} {direction} than database")
                else:
                    print(f"🧠 Grocery Intelligence: {len(discrepancies)} minor price differences logged")
            else:
                print("🧠 Grocery Intelligence: All prices match database")
        except Exception as e:
            print(f"⚠️  Grocery intelligence error: {e}")



def detect_grocery_only_mode():
    """Check if this should be grocery-only mode (no expense tracking)."""
    # Check for recent Signal messages with grocery-only keywords
    try:
        # Look for recent inbound media with grocery-only indicators
        inbound_dir = Path.home() / ".openclaw" / "media" / "inbound"
        
        # Check if there's a recent message file with grocery keywords
        recent_files = []
        for f in inbound_dir.glob("*.json"):
            if (datetime.now().timestamp() - f.stat().st_mtime) < 300:  # 5 minutes
                recent_files.append(f)
        
        grocery_keywords = [
            "grocery scan", "price scan", "grocery only", "price only",
            "no expense", "market research", "just prices", "prijscan"
        ]
        
        for msg_file in recent_files:
            try:
                with open(msg_file) as f:
                    msg_data = json.load(f)
                    msg_text = msg_data.get("text", "").lower()
                    if any(keyword in msg_text for keyword in grocery_keywords):
                        print("🛒 Detected grocery-only mode from Signal message")
                        return True
            except (json.JSONDecodeError, KeyError):
                continue
        
        return False
        
    except Exception:
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: receipt_processor.py <command> [args]")
        print("Commands: find, analyze, ocr, save, list, stats, cleanup")
        sys.exit(1)
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    
    commands = {
        "find": cmd_find,
        "analyze": cmd_analyze,
        "ocr": cmd_ocr,
        "save": cmd_save,
        "list": cmd_list,
        "stats": cmd_stats,
        "cleanup": cmd_cleanup
    }
    
    if cmd not in commands:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
    
    commands[cmd](args)


if __name__ == "__main__":
    main()
