#!/usr/bin/env python3
"""
Unified Dutch supermarket price checker.
Uses checkjebon.nl open data for AH, Jumbo, Hoogvliet, Lidl, Dirk, Plus, etc.

Usage:
    python3 supermarket-prices.py search "komkommer"
    python3 supermarket-prices.py search "kipfilet" --stores ah,jumbo,dirk
    python3 supermarket-prices.py compare "melk halfvol 1l"
    python3 supermarket-prices.py update  # refresh local cache
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
import urllib.request
import re

CACHE_DIR = Path.home() / ".openclaw/workspace/data"
CACHE_FILE = CACHE_DIR / "supermarkets-cache.json"
CHECKJEBON_URL = "https://raw.githubusercontent.com/supermarkt/checkjebon/refs/heads/main/data/supermarkets.json"
CACHE_MAX_AGE_HOURS = 24

# Store display names
STORE_NAMES = {
    "ah": "Albert Heijn",
    "aldi": "Aldi",
    "dekamarkt": "DekaMarkt",
    "dirk": "Dirk",
    "ekoplaza": "Ekoplaza",
    "hoogvliet": "Hoogvliet",
    "jumbo": "Jumbo",
    "lidl": "Lidl",
    "plus": "Plus",
    "poiesz": "Poiesz",
    "spar": "Spar",
    "vomar": "Vomar"
}

# Default stores for Default family (budget > nearby > convenient)
DEFAULT_STORES = ["dirk", "lidl", "hoogvliet", "ah", "jumbo"]

def load_cache():
    """Load cached supermarket data if fresh enough."""
    if not CACHE_FILE.exists():
        return None
    
    try:
        with open(CACHE_FILE) as f:
            cache = json.load(f)
        
        cached_at = datetime.fromisoformat(cache.get("cached_at", "2000-01-01"))
        if datetime.now() - cached_at > timedelta(hours=CACHE_MAX_AGE_HOURS):
            return None
        
        return cache.get("data")
    except Exception:
        return None

def update_cache():
    """Download fresh data from checkjebon."""
    print("Downloading supermarket data from checkjebon.nl...", file=sys.stderr)
    
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        with urllib.request.urlopen(CHECKJEBON_URL, timeout=60) as response:
            data = json.loads(response.read().decode())
        
        # Convert to dict keyed by store name
        store_data = {store["n"]: store["d"] for store in data}
        
        cache = {
            "cached_at": datetime.now().isoformat(),
            "data": store_data
        }
        
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f)
        
        total = sum(len(products) for products in store_data.values())
        print(f"Cached {total:,} products from {len(store_data)} stores.", file=sys.stderr)
        
        return store_data
    except Exception as e:
        print(f"Error downloading data: {e}", file=sys.stderr)
        return None

def get_data():
    """Get supermarket data, using cache or downloading fresh."""
    data = load_cache()
    if data is None:
        data = update_cache()
    return data

def search_products(query, stores=None, limit=5):
    """Search for products matching query."""
    data = get_data()
    if not data:
        print("No data available", file=sys.stderr)
        return []
    
    # Normalize query for matching
    query_lower = query.lower()
    query_words = query_lower.split()
    
    results = []
    
    for store_key, products in data.items():
        if stores and store_key not in stores:
            continue
        
        store_name = STORE_NAMES.get(store_key, store_key)
        
        for product in products:
            name = product.get("n", "").lower()
            
            # Check if all query words appear in product name
            if all(word in name for word in query_words):
                results.append({
                    "store": store_key,
                    "store_name": store_name,
                    "name": product.get("n"),
                    "price": product.get("p"),
                    "size": product.get("s", ""),
                    "link": product.get("l", "")
                })
    
    # Sort by price
    results.sort(key=lambda x: x.get("price", 999))
    
    return results[:limit] if limit else results

def compare_prices(query, stores=None, limit=None, as_json=False):
    """Compare prices across stores for a product."""
    results = search_products(query, stores, limit=None)
    
    if not results:
        if as_json:
            print(json.dumps({"error": f"No products found for: {query}"}, ensure_ascii=False))
        else:
            print(f"No products found for: {query}")
        return []
    
    # Group by store, show cheapest per store
    by_store = {}
    for r in results:
        store = r["store"]
        if store not in by_store or r["price"] < by_store[store]["price"]:
            by_store[store] = r
    
    # Sort stores by price
    sorted_stores = sorted(by_store.values(), key=lambda x: x["price"])
    
    if limit:
        sorted_stores = sorted_stores[:limit]
    
    if as_json:
        print(json.dumps(sorted_stores, indent=2, ensure_ascii=False))
        return sorted_stores
    
    print(f"\n🔍 Prijsvergelijking: {query}\n")
    print(f"{'Winkel':<15} {'Prijs':>8}  {'Product':<40} {'Maat'}")
    print("-" * 80)
    
    for i, item in enumerate(sorted_stores):
        marker = "🏆" if i == 0 else "  "
        print(f"{marker}{item['store_name']:<13} €{item['price']:>6.2f}  {item['name'][:40]:<40} {item['size']}")
    
    return sorted_stores


def find_deals(stores=None, limit=20, as_json=False):
    """Find products that appear to be on sale (low prices, common items)."""
    data = get_data()
    if not data:
        if as_json:
            print(json.dumps({"error": "No data available"}, ensure_ascii=False))
        return []
    
    # Look for typical "aanbieding" indicators or very low prices
    # Since checkjebon doesn't have explicit deal markers, we find suspiciously cheap items
    deals = []
    
    # Common products and their "normal" price thresholds
    deal_keywords = {
        "melk": 1.20,
        "brood": 1.50,
        "kaas": 3.00,
        "boter": 2.00,
        "eieren": 2.50,
        "kip": 4.00,
        "gehakt": 4.00,
        "pasta": 1.00,
        "rijst": 1.50,
        "bier": 0.80,
        "cola": 1.00,
        "chips": 1.50,
        "pizza": 2.50,
        "yoghurt": 1.00,
        "appels": 1.50,
        "bananen": 1.50,
    }
    
    for store_key, products in data.items():
        if stores and store_key not in stores:
            continue
        
        store_name = STORE_NAMES.get(store_key, store_key)
        
        for product in products:
            name = product.get("n", "").lower()
            price = product.get("p", 999)
            
            # Check if product matches a deal keyword and is below threshold
            for keyword, threshold in deal_keywords.items():
                if keyword in name and price < threshold * 0.75:  # 25% below normal
                    deals.append({
                        "store": store_key,
                        "store_name": store_name,
                        "name": product.get("n"),
                        "price": price,
                        "size": product.get("s", ""),
                        "link": product.get("l", ""),
                        "category": keyword
                    })
                    break
    
    # Sort by price, dedupe similar items
    deals.sort(key=lambda x: x["price"])
    
    # Limit results
    deals = deals[:limit] if limit else deals
    
    if as_json:
        print(json.dumps(deals, indent=2, ensure_ascii=False))
        return deals
    
    if not deals:
        print("Geen opvallende aanbiedingen gevonden.")
        return []
    
    print(f"\n🏷️  Mogelijke aanbiedingen:\n")
    for d in deals:
        print(f"  €{d['price']:.2f} @ {d['store_name']}: {d['name']} ({d['size']})")
    
    return deals

def main():
    parser = argparse.ArgumentParser(description="Dutch supermarket price checker")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for products")
    search_parser.add_argument("query", help="Product to search for")
    search_parser.add_argument("--stores", help="Comma-separated store list (ah,jumbo,dirk,hoogvliet,lidl)")
    search_parser.add_argument("--limit", type=int, default=10, help="Max results")
    search_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare prices across stores")
    compare_parser.add_argument("query", help="Product to compare")
    compare_parser.add_argument("--stores", help="Comma-separated store list")
    compare_parser.add_argument("--limit", type=int, help="Max results")
    compare_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # Deals command
    deals_parser = subparsers.add_parser("deals", help="Find current deals/aanbiedingen")
    deals_parser.add_argument("--stores", help="Comma-separated store list")
    deals_parser.add_argument("--limit", type=int, default=20, help="Max results")
    deals_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Refresh local cache")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show cache statistics")
    
    args = parser.parse_args()
    
    if args.command == "update":
        update_cache()
        
    elif args.command == "stats":
        data = get_data()
        if data:
            print("\n📊 Supermarkt data statistieken:\n")
            for store, products in sorted(data.items()):
                name = STORE_NAMES.get(store, store)
                print(f"  {name:<15} {len(products):>6,} producten")
            print(f"\n  {'TOTAAL':<15} {sum(len(p) for p in data.values()):>6,} producten")
            
            if CACHE_FILE.exists():
                mtime = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)
                print(f"\n  Cache: {CACHE_FILE}")
                print(f"  Updated: {mtime.strftime('%Y-%m-%d %H:%M')}")
    
    elif args.command == "search":
        stores = args.stores.split(",") if args.stores else DEFAULT_STORES
        results = search_products(args.query, stores, args.limit)
        
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            if not results:
                print(f"Geen producten gevonden voor: {args.query}")
            else:
                print(f"\n🔍 Zoekresultaten: {args.query}\n")
                for r in results:
                    print(f"  €{r['price']:.2f} @ {r['store_name']}: {r['name']} ({r['size']})")
    
    elif args.command == "compare":
        stores = args.stores.split(",") if args.stores else DEFAULT_STORES
        compare_prices(args.query, stores, args.limit, args.json)
    
    elif args.command == "deals":
        stores = args.stores.split(",") if args.stores else DEFAULT_STORES
        find_deals(stores, args.limit, args.json)

if __name__ == "__main__":
    main()
