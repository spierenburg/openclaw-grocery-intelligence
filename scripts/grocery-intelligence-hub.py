#!/usr/bin/env python3
"""
Grocery Intelligence Hub - Central command for all grocery intelligence operations.
Integrates price checking, feedback generation, community API, and receipt processing.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

class GroceryIntelligenceHub:
    def __init__(self):
        self.workspace = Path.cwd()
        self.scripts_dir = self.workspace / "scripts"
        
    def run_script(self, script_name, args=None, capture_output=False):
        """Run a script with arguments."""
        script_path = self.scripts_dir / script_name
        if not script_path.exists():
            print(f"❌ Script not found: {script_path}")
            return None
        
        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)
        
        if capture_output:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result
        else:
            subprocess.run(cmd)
            return None
    
    def price_check(self, product, stores=None, limit=5):
        """Check prices across stores."""
        print(f"🔍 Checking prices for: {product}")
        
        args = ["search", product, "--limit", str(limit)]
        if stores:
            args.extend(["--stores", ",".join(stores)])
        
        self.run_script("supermarket-prices.py", args)
    
    def price_compare(self, product, stores=None):
        """Compare prices across stores."""
        print(f"📊 Comparing prices for: {product}")
        
        args = ["compare", product]
        if stores:
            args.extend(["--stores", ",".join(stores)])
        
        self.run_script("supermarket-prices.py", args)
    
    def generate_feedback(self, receipt_path, store_name):
        """Generate feedback from receipt."""
        print(f"🧾 Generating feedback for {store_name} receipt: {receipt_path}")
        
        self.run_script("grocery-feedback.py", ["verify", receipt_path, store_name])
    
    def submit_feedback(self):
        """Submit accumulated feedback to community."""
        print("🚀 Submitting feedback to community database...")
        
        self.run_script("grocery-feedback.py", ["submit"])
    
    def feedback_stats(self):
        """Show feedback statistics."""
        print("📊 Feedback Statistics:")
        
        self.run_script("grocery-feedback.py", ["stats"])
    
    def start_community_api(self):
        """Start community API server."""
        print("🌐 Starting Community API server...")
        print("API will be available at: http://localhost:5000")
        print("Press Ctrl+C to stop")
        
        self.run_script("grocery-community-api.py")
    
    def process_receipt_with_intelligence(self, receipt_path, store_name=None):
        """Process receipt with full intelligence pipeline."""
        print(f"🎯 Full intelligence processing for: {receipt_path}")
        
        # Step 1: Generate feedback
        if store_name:
            self.generate_feedback(receipt_path, store_name)
        else:
            print("⚠️  Store name not provided, skipping feedback generation")
        
        # Step 2: Show feedback stats
        self.feedback_stats()
        
        # Step 3: Optionally submit feedback
        print("\n💭 Submit this feedback to community? (y/n): ", end="")
        if input().lower().startswith('y'):
            self.submit_feedback()
    
    def batch_process_receipts(self, receipts_dir):
        """Process all receipts in a directory."""
        receipts_dir = Path(receipts_dir)
        if not receipts_dir.exists():
            print(f"❌ Directory not found: {receipts_dir}")
            return
        
        print(f"📂 Batch processing receipts from: {receipts_dir}")
        
        # Find receipt files
        receipt_files = list(receipts_dir.glob("*.jpg")) + list(receipts_dir.glob("*.png"))
        print(f"Found {len(receipt_files)} receipt images")
        
        for i, receipt_file in enumerate(receipt_files, 1):
            print(f"\n--- Processing {i}/{len(receipt_files)}: {receipt_file.name} ---")
            
            # Try to detect store from filename or ask user
            store_name = self.detect_store_from_filename(receipt_file.name)
            if not store_name:
                print(f"Store name for {receipt_file.name} (or 'skip'): ", end="")
                store_name = input().strip().lower()
                if store_name == 'skip':
                    continue
            
            self.generate_feedback(str(receipt_file), store_name)
        
        # Show final stats and offer to submit all
        print(f"\n📊 Batch processing completed ({len(receipt_files)} receipts)")
        self.feedback_stats()
        
        print("\n💭 Submit all feedback to community? (y/n): ", end="")
        if input().lower().startswith('y'):
            self.submit_feedback()
    
    def detect_store_from_filename(self, filename):
        """Try to detect store name from receipt filename."""
        filename_lower = filename.lower()
        
        store_keywords = {
            'lidl': 'lidl',
            'ah': 'ah',
            'albert': 'ah',
            'heijn': 'ah',
            'jumbo': 'jumbo',
            'dirk': 'dirk',
            'hoogvliet': 'hoogvliet',
            'aldi': 'aldi',
            'plus': 'plus'
        }
        
        for keyword, store in store_keywords.items():
            if keyword in filename_lower:
                return store
        
        return None
    
    def interactive_mode(self):
        """Run in interactive mode."""
        print("🛒 Grocery Intelligence Hub - Interactive Mode")
        print("=" * 50)
        
        while True:
            print("\nAvailable commands:")
            print("  1. price <product>           - Check prices")
            print("  2. compare <product>         - Compare prices across stores")
            print("  3. feedback <receipt> <store> - Generate feedback from receipt")
            print("  4. submit                    - Submit feedback to community")
            print("  5. stats                     - Show feedback statistics")
            print("  6. api                       - Start community API server")
            print("  7. process <receipt> [store] - Full intelligence processing")
            print("  8. batch <directory>         - Batch process receipts")
            print("  9. quit                      - Exit")
            
            try:
                command = input("\n🤖 Enter command: ").strip().split()
                if not command:
                    continue
                
                cmd = command[0].lower()
                
                if cmd == 'quit' or cmd == 'q':
                    break
                elif cmd == 'price' and len(command) > 1:
                    self.price_check(" ".join(command[1:]))
                elif cmd == 'compare' and len(command) > 1:
                    self.price_compare(" ".join(command[1:]))
                elif cmd == 'feedback' and len(command) >= 3:
                    self.generate_feedback(command[1], command[2])
                elif cmd == 'submit':
                    self.submit_feedback()
                elif cmd == 'stats':
                    self.feedback_stats()
                elif cmd == 'api':
                    self.start_community_api()
                elif cmd == 'process' and len(command) >= 2:
                    store = command[2] if len(command) > 2 else None
                    self.process_receipt_with_intelligence(command[1], store)
                elif cmd == 'batch' and len(command) > 1:
                    self.batch_process_receipts(command[1])
                else:
                    print("❌ Invalid command or missing arguments")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Grocery Intelligence Hub - Central command for grocery operations"
    )
    
    parser.add_argument('command', nargs='?', 
                       choices=['price', 'compare', 'feedback', 'submit', 'stats', 'api', 'process', 'batch', 'interactive'],
                       help='Command to run')
    parser.add_argument('args', nargs='*', help='Command arguments')
    parser.add_argument('--stores', help='Comma-separated list of stores to check')
    parser.add_argument('--limit', type=int, default=5, help='Limit number of results')
    
    args = parser.parse_args()
    
    hub = GroceryIntelligenceHub()
    
    if not args.command:
        hub.interactive_mode()
        return
    
    # Parse stores
    stores = args.stores.split(',') if args.stores else None
    
    try:
        if args.command == 'price':
            if not args.args:
                print("❌ Please specify a product to search for")
                return
            product = " ".join(args.args)
            hub.price_check(product, stores, args.limit)
            
        elif args.command == 'compare':
            if not args.args:
                print("❌ Please specify a product to compare")
                return
            product = " ".join(args.args)
            hub.price_compare(product, stores)
            
        elif args.command == 'feedback':
            if len(args.args) < 2:
                print("❌ Please specify receipt path and store name")
                return
            hub.generate_feedback(args.args[0], args.args[1])
            
        elif args.command == 'submit':
            hub.submit_feedback()
            
        elif args.command == 'stats':
            hub.feedback_stats()
            
        elif args.command == 'api':
            hub.start_community_api()
            
        elif args.command == 'process':
            if not args.args:
                print("❌ Please specify receipt path")
                return
            receipt_path = args.args[0]
            store_name = args.args[1] if len(args.args) > 1 else None
            hub.process_receipt_with_intelligence(receipt_path, store_name)
            
        elif args.command == 'batch':
            if not args.args:
                print("❌ Please specify receipts directory")
                return
            hub.batch_process_receipts(args.args[0])
            
        elif args.command == 'interactive':
            hub.interactive_mode()
            
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()