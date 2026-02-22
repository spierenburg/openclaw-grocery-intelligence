#!/usr/bin/env python3
"""
Receipt Processor for OpenClaw
Finds and processes receipt images from Signal/OpenClaw inbound media.
Uses local Ollama vision model for privacy-first OCR.
"""

import base64
import json
import math
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path


# Grocery Intelligence Integration
# Catch all exceptions from exec_module — SyntaxError, AttributeError, and other
# module-level errors must not escape and crash the importer (#6).
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


def validate_image_path(path_str: str) -> str:
    """Resolve path and verify it is inside INBOUND_DIR to prevent path traversal."""
    resolved = Path(path_str).resolve()
    try:
        resolved.relative_to(INBOUND_DIR.resolve())
    except ValueError:
        raise ValueError(f"Image path must be inside {INBOUND_DIR}: {resolved}")
    return str(resolved)


def _sanitize_for_display(s: str, max_len: int = 200) -> str:
    """Strip ANSI/VT control sequences and truncate for safe terminal display."""
    s = re.sub(r'\x1b\][^\x07]*\x07', '', s)      # OSC sequences
    s = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', s)   # CSI sequences
    s = s.replace('\x1b', '')                       # bare ESC
    return s[:max_len]


def find_recent_image(max_age_seconds: int = 300) -> dict | None:
    """Find the most recent image in the inbound folder."""
    now = datetime.now().timestamp()
    candidates = []

    if not INBOUND_DIR.exists():
        return None

    for f in INBOUND_DIR.iterdir():
        if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
            # Findings #1/#2: resolve symlinks and verify path stays within INBOUND_DIR
            try:
                safe_path = validate_image_path(str(f))
            except ValueError:
                continue  # skip symlinks that escape INBOUND_DIR
            mtime = f.stat().st_mtime
            age = now - mtime
            if age <= max_age_seconds:
                candidates.append({
                    "path": safe_path,
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
    if any(c in image_path for c in ('\x00', '\n', '\r')):
        raise ValueError(f"Illegal character in image path: {image_path!r}")
    result = subprocess.run(
        ["/opt/homebrew/bin/tesseract", image_path, "stdout", "-l", "nld+eng"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Tesseract failed (exit {result.returncode}): {result.stderr.strip()}")
    return result.stdout.strip()


# Ollama config — set OLLAMA_URL in environment to override (never hardcode IPs in source)
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
VISION_MODEL = os.environ.get("OLLAMA_VISION_MODEL", "llama3.2-vision:11b")

_MODEL_RE = re.compile(r'^[a-zA-Z0-9._:/-]{1,100}$')
if not _MODEL_RE.match(VISION_MODEL):
    raise ValueError(f"OLLAMA_VISION_MODEL contains unsafe characters: {VISION_MODEL!r}")

_ALLOWED_OLLAMA_HOSTS = {"localhost", "127.0.0.1"}


def _validate_ollama_url(url: str) -> None:
    """Finding #2: prevent SSRF — Ollama endpoint must be localhost only."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"OLLAMA_URL scheme not allowed: {parsed.scheme!r}")
    if parsed.hostname not in _ALLOWED_OLLAMA_HOSTS:
        raise ValueError(
            f"OLLAMA_URL host not in allowlist (must be localhost or 127.0.0.1): {parsed.hostname!r}"
        )


_validate_ollama_url(OLLAMA_URL)


_VALID_CATEGORIES = {
    "boodschappen", "horeca", "transport", "klussen",
    "wonen", "kleding", "elektronica", "gezondheid", "overig"
}
_MAX_ITEMS = 200
_MAX_STR = 500


def _validate_llm_response(parsed: dict) -> dict:
    """Finding #12: enforce schema on LLM output to prevent second-order injection."""
    if not isinstance(parsed, dict):
        raise ValueError("LLM response is not a JSON object")
    if not parsed.get("is_receipt"):
        return {"is_receipt": False}
    validated: dict = {"is_receipt": True}
    if "store" in parsed:
        validated["store"] = str(parsed["store"])[:_MAX_STR]
    if "date" in parsed:
        if re.match(r'^\d{4}-\d{2}-\d{2}$', str(parsed["date"])):
            validated["date"] = parsed["date"]
    if "time" in parsed:
        validated["time"] = str(parsed["time"])[:10]
    if "amount" in parsed:
        amount = float(parsed["amount"])
        if not (0 <= amount <= 100_000):
            raise ValueError(f"Implausible amount: {amount}")
        validated["amount"] = amount
    if "items" in parsed:
        if not isinstance(parsed["items"], list):
            raise ValueError("items must be a list")
        validated["items"] = [str(i)[:_MAX_STR] for i in parsed["items"][:_MAX_ITEMS]]
    if "category" in parsed:
        validated["category"] = parsed["category"] if parsed["category"] in _VALID_CATEGORIES else "overig"
    return validated


def _validated_int(value: str, min_val: int, max_val: int, default: int) -> int:
    """Finding #10: clamp CLI integer args to a safe range."""
    try:
        n = int(value)
        if not (min_val <= n <= max_val):
            raise ValueError(f"{n} out of range [{min_val}, {max_val}]")
        return n
    except (TypeError, ValueError):
        return default


def analyze_with_ollama(image_path: str) -> dict:
    """Analyze receipt image using local Ollama vision model."""

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
                    # Finding #12: validate LLM output before returning
                    return _validate_llm_response(json.loads(json_str))
                except (json.JSONDecodeError, ValueError):
                    pass

            # Fallback: parse structured text response
            parsed = {"is_receipt": True, "raw": response_text}

            # Extract store
            store_match = re.search(r'\*\*Store\*\*[:\s]+([^\n*]+)', response_text, re.I)
            if store_match:
                parsed["store"] = store_match.group(1).strip()[:200]

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
                raw_amount = float(amount_match.group(1).replace(",", "."))
                if math.isfinite(raw_amount) and 0 <= raw_amount <= 100_000:
                    parsed["amount"] = raw_amount

            # Finding #3: route fallback through the same schema validator as the primary path
            try:
                return _validate_llm_response(parsed)
            except (ValueError, TypeError):
                return {"is_receipt": False, "error": "Could not parse LLM response into valid receipt schema"}

    except Exception as exc:
        # Don't leak internal IP or error details to caller; log to stderr for diagnostics
        print(f"[ollama] {type(exc).__name__}: {exc}", file=sys.stderr)
        return {"error": "Analysis service unavailable"}


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
    ext = src.suffix.lower()
    _SAFE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    if ext not in _SAFE_EXTENSIONS:
        raise ValueError(f"Unsupported image extension: {ext!r}")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    new_filename = f"receipt-{timestamp}{ext}"
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
    max_age = _validated_int(args[0], 1, 86_400, 300) if args else 300
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
        try:
            image_path = validate_image_path(args[0])
        except ValueError as e:
            print(json.dumps({"error": str(e)}))
            sys.exit(1)

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
        try:
            image_path = validate_image_path(args[0])
        except ValueError as e:
            print(json.dumps({"error": str(e)}))
            sys.exit(1)

    text = run_tesseract(image_path)
    print(json.dumps({
        "image": image_path,
        "ocr_text": text,
        "lines": len(text.split("\n")) if text else 0
    }, indent=2))


ALLOWED_RECEIPT_KEYS = {"store", "date", "time", "amount", "items", "category", "is_receipt"}
VALID_CATEGORIES = {
    "boodschappen", "horeca", "transport", "klussen",
    "wonen", "kleding", "elektronica", "gezondheid", "overig"
}


def validate_receipt_data(data: dict) -> dict:
    """Strip unknown keys and enforce types to prevent second-order injection."""
    if not isinstance(data, dict):
        raise ValueError("Receipt data must be a JSON object")
    sanitized = {k: v for k, v in data.items() if k in ALLOWED_RECEIPT_KEYS}
    if "amount" in sanitized:
        # Finding #5: reject inf/nan and out-of-range values
        amount = float(sanitized["amount"])
        if not (math.isfinite(amount) and 0.0 <= amount <= 100_000.0):
            raise ValueError(f"amount out of acceptable range [0, 100000]: {amount}")
        sanitized["amount"] = amount
    if "items" in sanitized:
        if not isinstance(sanitized["items"], list):
            raise ValueError("items must be a list")
        sanitized["items"] = [str(i)[:200] for i in sanitized["items"]]
    if "category" in sanitized and sanitized["category"] not in VALID_CATEGORIES:
        sanitized["category"] = "overig"
    return sanitized


def cmd_save(args):
    """Save a receipt. Expects JSON as first arg or stdin."""
    if args:
        try:
            data = validate_receipt_data(json.loads(args[0]))
        except (json.JSONDecodeError, ValueError) as e:
            print(json.dumps({"error": f"Invalid receipt data: {e}"}))
            sys.exit(1)
        if len(args) > 1:
            # Finding #1: apply same path guard as cmd_analyze / cmd_ocr
            try:
                image_path = validate_image_path(args[1])
            except ValueError as e:
                print(json.dumps({"error": str(e)}))
                sys.exit(1)
        else:
            image_path = None
    else:
        try:
            data = validate_receipt_data(json.load(sys.stdin))
        except (json.JSONDecodeError, ValueError) as e:
            print(json.dumps({"error": f"Invalid receipt data: {e}"}))
            sys.exit(1)
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
    limit = _validated_int(args[0], 1, 10_000, 10) if args else 10
    
    if not RECEIPTS_JSONL.exists():
        print(json.dumps({"receipts": [], "total": 0}))
        return
    
    receipts = []
    with open(RECEIPTS_JSONL) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                receipts.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # skip malformed lines (#3)

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
            if not line:
                continue
            try:
                receipts.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # skip malformed lines (#3)

    total_amount = 0
    by_store = {}
    by_category = {}
    
    for r in receipts:
        amount = r.get("amount", 0)
        if isinstance(amount, str):
            # Parse "€12.50" format
            amount = float(amount.replace("€", "").replace(",", ".").strip())
        # Finding #5: skip corrupted/non-finite amounts rather than poisoning totals
        if not (math.isfinite(amount) and 0.0 <= amount <= 100_000.0):
            continue
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
    max_days = _validated_int(args[0], 1, 365, 30) if args else 30
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
                        safe_name = _sanitize_for_display(str(d['receipt_product']))  # #4
                        print(f"   • {safe_name}: €{abs(d['price_difference']):.2f} {direction} than database")
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
        
    except OSError:
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
