"""Tests for grocery_feedback.py - product matching and confidence scoring."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from grocery_feedback import find_best_product_match, calculate_match_confidence


class TestFindBestProductMatch:
    """Tests for find_best_product_match()."""

    def test_exact_match(self, sample_store_products):
        result = find_best_product_match("Melk Halfvol 1L", sample_store_products)
        assert result is not None
        assert result["name"] == "Melk Halfvol 1L"
        assert result["price"] == 1.89

    def test_partial_match(self, sample_store_products):
        result = find_best_product_match("Melk Halfvol", sample_store_products)
        assert result is not None
        assert "Melk" in result["name"]

    def test_case_insensitive(self, sample_store_products):
        result = find_best_product_match("melk halfvol 1l", sample_store_products)
        assert result is not None
        assert result["name"] == "Melk Halfvol 1L"

    def test_no_match(self, sample_store_products):
        result = find_best_product_match("Chocolade Hagelslag", sample_store_products)
        assert result is None

    def test_empty_product_list(self):
        result = find_best_product_match("Melk", [])
        assert result is None

    def test_empty_query(self, sample_store_products):
        result = find_best_product_match("", sample_store_products)
        assert result is None

    def test_threshold_boundary_below(self):
        """A single common word out of 4 total unique words = 0.25, below 0.3 threshold."""
        products = [{"n": "Gouda Kaas Jong Belegen", "p": 5.99, "s": ""}]
        result = find_best_product_match("Gouda Cheddar Extra", products)
        # 1 common word ("gouda") / 5 unique words = 0.20 < 0.30
        assert result is None

    def test_threshold_boundary_above(self):
        """Two common words out of 4 total unique words = 0.50, above 0.3 threshold."""
        products = [{"n": "Gouda Kaas Jong", "p": 5.99, "s": "400g"}]
        result = find_best_product_match("Gouda Kaas", products)
        # 2 common / 3 unique = 0.67 > 0.30
        assert result is not None
        assert result["price"] == 5.99

    def test_best_match_selected(self):
        """When multiple products match, the best scoring one is returned."""
        products = [
            {"n": "Melk Vol 1L", "p": 2.09, "s": "1L"},
            {"n": "Melk Halfvol 1L", "p": 1.89, "s": "1L"},
        ]
        result = find_best_product_match("Melk Halfvol 1L", products)
        assert result is not None
        assert result["price"] == 1.89


class TestCalculateMatchConfidence:
    """Tests for calculate_match_confidence()."""

    def test_identical_names(self):
        score = calculate_match_confidence("Melk Halfvol", "Melk Halfvol")
        assert score == 1.0

    def test_partial_overlap(self):
        score = calculate_match_confidence("Melk Halfvol", "Melk Halfvol 1L")
        assert 0.0 < score < 1.0

    def test_disjoint_names(self):
        score = calculate_match_confidence("Melk Halfvol", "Kipfilet Naturel")
        assert score == 0.0

    def test_empty_receipt_name(self):
        score = calculate_match_confidence("", "Melk Halfvol")
        assert score == 0.0

    def test_empty_product_name(self):
        score = calculate_match_confidence("Melk Halfvol", "")
        assert score == 0.0

    def test_both_empty(self):
        score = calculate_match_confidence("", "")
        assert score == 0.0

    def test_case_insensitive(self):
        score1 = calculate_match_confidence("MELK HALFVOL", "melk halfvol")
        score2 = calculate_match_confidence("melk halfvol", "melk halfvol")
        assert score1 == score2
