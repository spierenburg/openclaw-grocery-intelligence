"""Tests for receipt_processor.py - stats and list commands."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from receipt_processor import cmd_stats, cmd_list, RECEIPTS_JSONL


class TestCmdStats:
    """Tests for cmd_stats()."""

    def test_aggregation_by_store(self, sample_receipts_jsonl, capsys):
        with patch("receipt_processor.RECEIPTS_JSONL", sample_receipts_jsonl):
            cmd_stats([])
        output = json.loads(capsys.readouterr().out)
        assert output["by_store"]["Albert Heijn"] == 43.80  # 25.50 + 18.30
        assert output["by_store"]["Lidl"] == 32.10

    def test_aggregation_by_category(self, sample_receipts_jsonl, capsys):
        with patch("receipt_processor.RECEIPTS_JSONL", sample_receipts_jsonl):
            cmd_stats([])
        output = json.loads(capsys.readouterr().out)
        assert output["by_category"]["boodschappen"] == 75.90  # 25.50 + 18.30 + 32.10
        assert output["by_category"]["klussen"] == 15.00

    def test_total_amount(self, sample_receipts_jsonl, capsys):
        with patch("receipt_processor.RECEIPTS_JSONL", sample_receipts_jsonl):
            cmd_stats([])
        output = json.loads(capsys.readouterr().out)
        assert output["total_amount"] == 90.90
        assert output["total_receipts"] == 4

    def test_euro_string_parsing(self, tmp_path, capsys):
        """Amounts with euro sign string format should be parsed correctly."""
        jsonl_file = tmp_path / "receipts.jsonl"
        with open(jsonl_file, "w") as f:
            f.write(json.dumps({"store": "AH", "amount": "€12.50", "category": "food"}) + "\n")

        with patch("receipt_processor.RECEIPTS_JSONL", jsonl_file):
            cmd_stats([])
        output = json.loads(capsys.readouterr().out)
        assert output["total_amount"] == 12.50

    def test_empty_file(self, tmp_path, capsys):
        jsonl_file = tmp_path / "receipts.jsonl"
        jsonl_file.touch()
        with patch("receipt_processor.RECEIPTS_JSONL", jsonl_file):
            cmd_stats([])
        output = json.loads(capsys.readouterr().out)
        assert output["total_receipts"] == 0
        assert output["total_amount"] == 0


class TestCmdList:
    """Tests for cmd_list()."""

    def test_default_limit(self, sample_receipts_jsonl, capsys):
        with patch("receipt_processor.RECEIPTS_JSONL", sample_receipts_jsonl):
            cmd_list([])
        output = json.loads(capsys.readouterr().out)
        assert output["total"] == 4
        assert len(output["receipts"]) == 4

    def test_limit_parameter(self, sample_receipts_jsonl, capsys):
        with patch("receipt_processor.RECEIPTS_JSONL", sample_receipts_jsonl):
            cmd_list(["2"])
        output = json.loads(capsys.readouterr().out)
        assert output["total"] == 4
        assert len(output["receipts"]) == 2

    def test_reverse_ordering(self, sample_receipts_jsonl, capsys):
        """Most recent (last written) should appear first."""
        with patch("receipt_processor.RECEIPTS_JSONL", sample_receipts_jsonl):
            cmd_list([])
        output = json.loads(capsys.readouterr().out)
        # Last entry in file was Praxis, so it should be first in output
        assert output["receipts"][0]["store"] == "Praxis"

    def test_no_file(self, tmp_path, capsys):
        missing_file = tmp_path / "nonexistent.jsonl"
        with patch("receipt_processor.RECEIPTS_JSONL", missing_file):
            cmd_list([])
        output = json.loads(capsys.readouterr().out)
        assert output["receipts"] == []
        assert output["total"] == 0
