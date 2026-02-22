#!/usr/bin/env python3
"""
Grocery data feedback system - contribute improvements back to the community.
Compares receipt OCR data against checkjebon prices and reports discrepancies.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.parse

FEEDBACK_API = "https://api.example.com/v1/grocery-feedback"  # Placeholder
LOCAL_FEEDBACK_FILE = Path("memory/grocery-feedback.jsonl")

def verify_receipt_against_checkjebon(receipt_data, store_name):
    """Compare receipt prices against checkjebon data."""
    # Load checkjebon data
    checkjebon_file = Path("data/supermarkets-cache.json")
    if not checkjebon_file.exists():
        print("No checkjebon cache found. Run: python3 scripts/supermarket_prices.py update")
        return []
    
    with open(checkjebon_file) as f:
        cache = json.load(f)
        store_products = cache.get("data", {}).get(store_name.lower(), [])
    
    discrepancies = []
    
    for receipt_item in receipt_data:
        # Find matching product in checkjebon data  
        best_match = find_best_product_match(receipt_item['name'], store_products)
        
        if best_match:
            price_diff = abs(receipt_item['price'] - best_match['price'])
            if price_diff > 0.05:  # >5 cent difference
                discrepancy = {
                    "receipt_product": receipt_item['name'],
                    "receipt_price": receipt_item['price'],
                    "checkjebon_product": best_match['name'],
                    "checkjebon_price": best_match['price'],
                    "price_difference": price_diff,
                    "store": store_name,
                    "date": receipt_item.get('date', datetime.now().isoformat()),
                    "confidence": calculate_match_confidence(receipt_item['name'], best_match['name'])
                }
                discrepancies.append(discrepancy)
    
    return discrepancies

def find_best_product_match(receipt_name, store_products):
    """Find best matching product using fuzzy matching."""
    receipt_words = set(receipt_name.lower().split())
    best_match = None
    best_score = 0
    
    for product in store_products:
        product_words = set(product.get('n', '').lower().split())
        
        # Calculate word overlap score
        common_words = receipt_words.intersection(product_words)
        score = len(common_words) / max(len(receipt_words), len(product_words), 1)
        
        if score > best_score and score > 0.3:  # Minimum 30% word overlap
            best_score = score  
            best_match = {
                "name": product.get('n', ''),
                "price": product.get('p', 0),
                "size": product.get('s', ''),
            }
    
    return best_match

def calculate_match_confidence(receipt_name, product_name):
    """Calculate confidence score for product matching."""
    receipt_words = set(receipt_name.lower().split())
    product_words = set(product_name.lower().split())
    
    if not receipt_words or not product_words:
        return 0.0
        
    common_words = receipt_words.intersection(product_words)
    union_words = receipt_words.union(product_words)
    
    return len(common_words) / len(union_words)

def submit_feedback_locally(discrepancies):
    """Store feedback locally for later batch submission."""
    LOCAL_FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    feedback_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "price_discrepancy",
        "discrepancies": discrepancies,
        "source": "receipt_ocr",
        "status": "pending_submission"
    }
    
    # Append to JSONL file
    with open(LOCAL_FEEDBACK_FILE, "a") as f:
        f.write(json.dumps(feedback_entry) + "\n")
    
    print(f"Logged {len(discrepancies)} price discrepancies locally.")
    print(f"Total feedback entries: {count_pending_feedback()}")

_ALLOWED_API_HOSTS = {"localhost", "127.0.0.1"}


def _validate_api_url(api_url: str) -> None:
    """Prevent SSRF by restricting scheme and host."""
    parsed = urllib.parse.urlparse(api_url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme!r}")
    if parsed.hostname not in _ALLOWED_API_HOSTS:
        raise ValueError(f"API host not in allowlist: {parsed.hostname!r}")


def submit_feedback_to_community(batch_size=10, api_url="http://localhost:5000"):
    """Submit accumulated feedback to community database."""
    _validate_api_url(api_url)

    if not LOCAL_FEEDBACK_FILE.exists():
        print("No feedback to submit.")
        return
    
    pending_entries = []
    with open(LOCAL_FEEDBACK_FILE) as f:
        for line in f:
            entry = json.loads(line.strip())
            if entry.get("status") == "pending_submission":
                pending_entries.append(entry)
    
    if not pending_entries:
        print("No pending feedback to submit.")
        return
    
    print(f"🚀 Submitting {len(pending_entries)} feedback entries to community API...")
    
    # Submit in batches
    submitted_count = 0
    for i in range(0, len(pending_entries), batch_size):
        batch = pending_entries[i:i + batch_size]
        
        try:
            # Convert to API format
            corrections = []
            for entry in batch:
                for discrepancy in entry.get("discrepancies", []):
                    corrections.append({
                        "product_name": discrepancy["receipt_product"],
                        "store_chain": discrepancy["store"],
                        "actual_price": discrepancy["receipt_price"],
                        "checkjebon_price": discrepancy["checkjebon_price"],
                        "verified_date": discrepancy.get("date", "2026-02-20"),
                        "verification_method": "receipt_ocr",
                        "confidence_score": discrepancy.get("confidence", 0.5)
                    })
            
            if corrections:
                # Submit to community API
                payload = {
                    "corrections": corrections,
                    "contributor_id": "openclaw-system"
                }
                
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(
                    f"{api_url}/api/v1/submit-bulk",
                    data=data,
                    headers={'Content-Type': 'application/json'}
                )
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    result = json.loads(response.read().decode())
                    
                print(f"✅ Submitted {result.get('submitted', 0)} corrections")
                
                # Mark as submitted locally
                mark_entries_submitted([e["timestamp"] for e in batch])
                submitted_count += len(batch)
            
        except Exception as e:
            print(f"❌ Failed to submit batch: {e}")
            print(f"   (Is community API running at {api_url}?)")
            break
    
    print(f"📊 Successfully submitted {submitted_count} feedback entries to community database.")

def mark_entries_submitted(timestamps):
    """Mark feedback entries as submitted."""
    # Re-write file with updated status
    if not LOCAL_FEEDBACK_FILE.exists():
        return
        
    updated_entries = []
    with open(LOCAL_FEEDBACK_FILE) as f:
        for line in f:
            entry = json.loads(line.strip())
            if entry["timestamp"] in timestamps:
                entry["status"] = "submitted"
            updated_entries.append(entry)
    
    with open(LOCAL_FEEDBACK_FILE, "w") as f:
        for entry in updated_entries:
            f.write(json.dumps(entry) + "\n")

def count_pending_feedback():
    """Count pending feedback entries."""
    if not LOCAL_FEEDBACK_FILE.exists():
        return 0
    
    count = 0
    with open(LOCAL_FEEDBACK_FILE) as f:
        for line in f:
            entry = json.loads(line.strip())
            if entry.get("status") == "pending_submission":
                count += 1
    return count

_ALLOWED_RECEIPT_DIR = Path.home() / ".openclaw"


def analyze_receipt_file(receipt_path, store_name):
    """Analyze a receipt file and generate feedback."""
    # Try to load actual receipt data
    if receipt_path.endswith('.json'):
        resolved = Path(receipt_path).resolve()
        try:
            resolved.relative_to(_ALLOWED_RECEIPT_DIR.resolve())
        except ValueError:
            print(f"Receipt path must be within {_ALLOWED_RECEIPT_DIR}: {resolved}")
            return
        try:
            with open(resolved) as f:
                receipt_data = json.load(f)
        except FileNotFoundError:
            print(f"Receipt file not found: {receipt_path}")
            return
    else:
        # Fallback: simulate with example data
        print(f"Using simulated data for {receipt_path}")
        receipt_data = [
            {"name": "Melk Halfvol 1L", "price": 1.89, "date": "2026-02-20"},
            {"name": "Brood Wit", "price": 1.29, "date": "2026-02-20"},
            {"name": "Kaas Gouda Jong", "price": 4.99, "date": "2026-02-20"}
        ]
    
    discrepancies = verify_receipt_against_checkjebon(receipt_data, store_name)
    
    if discrepancies:
        print(f"\n🔍 Found {len(discrepancies)} price discrepancies:")
        for d in discrepancies:
            print(f"  • {d['receipt_product']}: €{d['receipt_price']:.2f} (receipt) vs €{d['checkjebon_price']:.2f} (checkjebon)")
            print(f"    Difference: €{d['price_difference']:.2f}, Confidence: {d['confidence']:.2f}")
        
        submit_feedback_locally(discrepancies)
    else:
        print("✅ All receipt prices match checkjebon data.")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 grocery_feedback.py verify <receipt_path> <store_name>")
        print("  python3 grocery_feedback.py submit")
        print("  python3 grocery_feedback.py stats")
        print("\nShowing current stats:")
        command = "stats"
    else:
        command = sys.argv[1]
    
    if command == "verify":
        if len(sys.argv) < 4:
            print("Error: verify command requires <receipt_path> and <store_name>")
            print("Example: python3 grocery_feedback.py verify ~/receipts/ah.jpg ah")
            sys.exit(1)
        receipt_path = sys.argv[2]
        store_name = sys.argv[3]
        analyze_receipt_file(receipt_path, store_name)
        
    elif command == "submit":
        submit_feedback_to_community()
        
    elif command == "stats":
        pending = count_pending_feedback()
        print(f"Pending feedback entries: {pending}")
        
        if LOCAL_FEEDBACK_FILE.exists():
            with open(LOCAL_FEEDBACK_FILE) as f:
                total = sum(1 for _ in f)
            print(f"Total feedback entries: {total}")
            print(f"Submitted: {total - pending}")
        else:
            print("No feedback file found yet.")

if __name__ == "__main__":
    main()