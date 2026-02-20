"""Tests for grocery_intelligence_hub.py - store detection."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from grocery_intelligence_hub import GroceryIntelligenceHub


class TestDetectStoreFromFilename:
    """Tests for detect_store_from_filename()."""

    def setup_method(self):
        self.hub = GroceryIntelligenceHub()

    def test_lidl(self):
        assert self.hub.detect_store_from_filename("receipt-lidl-20260220.jpg") == "lidl"

    def test_ah_keyword(self):
        assert self.hub.detect_store_from_filename("ah-bon-123.png") == "ah"

    def test_albert_keyword(self):
        assert self.hub.detect_store_from_filename("albert-heijn-receipt.jpg") == "ah"

    def test_heijn_keyword(self):
        assert self.hub.detect_store_from_filename("heijn_receipt.jpg") == "ah"

    def test_jumbo(self):
        assert self.hub.detect_store_from_filename("jumbo_20260220.jpg") == "jumbo"

    def test_dirk(self):
        assert self.hub.detect_store_from_filename("dirk-receipt.jpg") == "dirk"

    def test_hoogvliet(self):
        assert self.hub.detect_store_from_filename("hoogvliet_bon.png") == "hoogvliet"

    def test_aldi(self):
        assert self.hub.detect_store_from_filename("aldi-20260220.jpg") == "aldi"

    def test_plus(self):
        assert self.hub.detect_store_from_filename("plus-receipt.jpg") == "plus"

    def test_case_insensitive(self):
        assert self.hub.detect_store_from_filename("LIDL_RECEIPT.JPG") == "lidl"

    def test_no_match(self):
        assert self.hub.detect_store_from_filename("random-photo.jpg") is None

    def test_no_match_generic(self):
        assert self.hub.detect_store_from_filename("IMG_20260220_123456.jpg") is None
