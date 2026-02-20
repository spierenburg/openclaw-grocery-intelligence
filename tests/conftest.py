"""Shared fixtures for grocery intelligence tests."""

import pytest


@pytest.fixture
def sample_store_products():
    """Sample store products in checkjebon format."""
    return [
        {"n": "Melk Halfvol 1L", "p": 1.89, "s": "1L"},
        {"n": "Brood Wit Heel", "p": 1.29, "s": "800g"},
        {"n": "Kaas Gouda Jong", "p": 4.99, "s": "450g"},
        {"n": "Kipfilet", "p": 7.49, "s": "500g"},
        {"n": "Pasta Penne", "p": 0.89, "s": "500g"},
        {"n": "Rijst Basmati", "p": 1.79, "s": "1kg"},
    ]


@pytest.fixture
def sample_store_data():
    """Sample multi-store data dict (like get_data() returns)."""
    return {
        "ah": [
            {"n": "Melk Halfvol 1L", "p": 1.89, "s": "1L", "l": ""},
            {"n": "Kipfilet", "p": 7.49, "s": "500g", "l": ""},
            {"n": "Pasta Penne", "p": 0.99, "s": "500g", "l": ""},
        ],
        "lidl": [
            {"n": "Melk Halfvol 1L", "p": 1.59, "s": "1L", "l": ""},
            {"n": "Kipfilet", "p": 6.99, "s": "500g", "l": ""},
            {"n": "Pasta Penne", "p": 0.79, "s": "500g", "l": ""},
        ],
        "jumbo": [
            {"n": "Melk Halfvol 1L", "p": 1.79, "s": "1L", "l": ""},
            {"n": "Kipfilet", "p": 7.29, "s": "450g", "l": ""},
        ],
    }


@pytest.fixture
def sample_receipts_jsonl(tmp_path):
    """Create a temporary receipts JSONL file with sample data."""
    import json

    receipts = [
        {"store": "Albert Heijn", "amount": 25.50, "category": "boodschappen", "date": "2026-02-01"},
        {"store": "Albert Heijn", "amount": 18.30, "category": "boodschappen", "date": "2026-02-05"},
        {"store": "Lidl", "amount": 32.10, "category": "boodschappen", "date": "2026-02-03"},
        {"store": "Praxis", "amount": "€15.00", "category": "klussen", "date": "2026-02-04"},
    ]

    jsonl_file = tmp_path / "receipts.jsonl"
    with open(jsonl_file, "w") as f:
        for r in receipts:
            f.write(json.dumps(r) + "\n")

    return jsonl_file
