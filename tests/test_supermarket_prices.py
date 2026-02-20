"""Tests for supermarket_prices.py - search, compare, and deals functions."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from supermarket_prices import search_products, compare_prices, find_deals


class TestSearchProducts:
    """Tests for search_products()."""

    def test_single_word_search(self, sample_store_data):
        with patch("supermarket_prices.get_data", return_value=sample_store_data):
            results = search_products("melk")
        assert len(results) > 0
        assert all("melk" in r["name"].lower() for r in results)

    def test_multi_word_search(self, sample_store_data):
        with patch("supermarket_prices.get_data", return_value=sample_store_data):
            results = search_products("melk halfvol")
        assert len(results) > 0
        for r in results:
            name_lower = r["name"].lower()
            assert "melk" in name_lower and "halfvol" in name_lower

    def test_case_insensitive(self, sample_store_data):
        with patch("supermarket_prices.get_data", return_value=sample_store_data):
            results_lower = search_products("melk")
            results_upper = search_products("MELK")
        assert len(results_lower) == len(results_upper)

    def test_no_results(self, sample_store_data):
        with patch("supermarket_prices.get_data", return_value=sample_store_data):
            results = search_products("chocoladereep")
        assert results == []

    def test_limit_parameter(self, sample_store_data):
        with patch("supermarket_prices.get_data", return_value=sample_store_data):
            results = search_products("melk", limit=2)
        assert len(results) <= 2

    def test_store_filter(self, sample_store_data):
        with patch("supermarket_prices.get_data", return_value=sample_store_data):
            results = search_products("melk", stores=["lidl"])
        assert all(r["store"] == "lidl" for r in results)

    def test_sorted_by_price(self, sample_store_data):
        with patch("supermarket_prices.get_data", return_value=sample_store_data):
            results = search_products("melk")
        prices = [r["price"] for r in results]
        assert prices == sorted(prices)

    def test_no_data_available(self):
        with patch("supermarket_prices.get_data", return_value=None):
            results = search_products("melk")
        assert results == []


class TestComparePrices:
    """Tests for compare_prices()."""

    def test_store_deduplication(self, sample_store_data):
        """Each store should appear at most once (cheapest product per store)."""
        with patch("supermarket_prices.get_data", return_value=sample_store_data):
            results = compare_prices("melk", as_json=True)
        stores = [r["store"] for r in results]
        assert len(stores) == len(set(stores))

    def test_cheapest_per_store(self, sample_store_data):
        """compare_prices keeps only the cheapest product per store."""
        with patch("supermarket_prices.get_data", return_value=sample_store_data):
            results = compare_prices("pasta", as_json=True)
        for r in results:
            if r["store"] == "lidl":
                assert r["price"] == 0.79

    def test_sorted_by_price(self, sample_store_data):
        with patch("supermarket_prices.get_data", return_value=sample_store_data):
            results = compare_prices("melk", as_json=True)
        prices = [r["price"] for r in results]
        assert prices == sorted(prices)

    def test_empty_results(self, sample_store_data):
        with patch("supermarket_prices.get_data", return_value=sample_store_data):
            results = compare_prices("nonexistent_product_xyz", as_json=True)
        assert results == []

    def test_limit_parameter(self, sample_store_data):
        with patch("supermarket_prices.get_data", return_value=sample_store_data):
            results = compare_prices("melk", limit=1, as_json=True)
        assert len(results) <= 1


class TestFindDeals:
    """Tests for find_deals()."""

    def test_finds_deals_below_threshold(self):
        """Products priced below 75% of keyword threshold should be deals."""
        data = {
            "lidl": [
                {"n": "Melk Halfvol 1L", "p": 0.80, "s": "1L", "l": ""},  # threshold 1.20, 75% = 0.90
            ]
        }
        with patch("supermarket_prices.get_data", return_value=data):
            results = find_deals(as_json=True)
        assert len(results) == 1
        assert results[0]["category"] == "melk"

    def test_no_deals_above_threshold(self):
        """Products priced above 75% of threshold should not appear."""
        data = {
            "ah": [
                {"n": "Melk Halfvol 1L", "p": 1.15, "s": "1L", "l": ""},  # threshold 1.20, 75% = 0.90
            ]
        }
        with patch("supermarket_prices.get_data", return_value=data):
            results = find_deals(as_json=True)
        assert results == []

    def test_keyword_matching(self):
        """Only products matching deal keywords are considered."""
        data = {
            "ah": [
                {"n": "Luxe Zeep", "p": 0.10, "s": "", "l": ""},  # cheap but no keyword match
            ]
        }
        with patch("supermarket_prices.get_data", return_value=data):
            results = find_deals(as_json=True)
        assert results == []

    def test_store_filter(self):
        data = {
            "ah": [{"n": "Melk 1L", "p": 0.50, "s": "1L", "l": ""}],
            "lidl": [{"n": "Melk 1L", "p": 0.50, "s": "1L", "l": ""}],
        }
        with patch("supermarket_prices.get_data", return_value=data):
            results = find_deals(stores=["lidl"], as_json=True)
        assert all(r["store"] == "lidl" for r in results)

    def test_limit_parameter(self):
        data = {
            "ah": [
                {"n": "Melk 1L", "p": 0.50, "s": "1L", "l": ""},
                {"n": "Brood Wit", "p": 0.50, "s": "", "l": ""},
                {"n": "Pasta Penne", "p": 0.30, "s": "500g", "l": ""},
            ]
        }
        with patch("supermarket_prices.get_data", return_value=data):
            results = find_deals(limit=1, as_json=True)
        assert len(results) <= 1
