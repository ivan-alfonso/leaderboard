"""
Tests for agent/intents/entity_utils.py

Run from leaderboard/agent/:
    python -m pytest tests/test_entity_utils.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from intents.entity_utils import (
    extract_cefr_level,
    extract_category,
    extract_licensing,
    extract_top_n,
    extract_ascending,
    resolve_model_name,
)


# ── extract_cefr_level ────────────────────────────────────────────────────────

class TestExtractCefrLevel:
    def test_uppercase_token(self):
        assert extract_cefr_level("What is the B2 score?") == "B2"

    def test_all_levels_detected(self):
        for lvl in ("A1", "A2", "B1", "B2", "C1", "C2"):
            assert extract_cefr_level(f"Score at {lvl}") == lvl

    def test_spelled_out_intermediate(self):
        assert extract_cefr_level("intermediate level results") == "B1"

    def test_spelled_out_advanced(self):
        assert extract_cefr_level("advanced CEFR performance") == "C1"

    def test_no_level_returns_none(self):
        assert extract_cefr_level("Show me the top models") is None

    def test_lowercase_level_detected(self):
        assert extract_cefr_level("b2 grammar score") == "B2"


# ── extract_category ──────────────────────────────────────────────────────────

class TestExtractCategory:
    def test_grammar(self):
        assert extract_category("grammar results at B1") == "Grammar"

    def test_reading_alias(self):
        assert extract_category("reading comprehension score") == "RC"

    def test_listening_alias(self):
        assert extract_category("listening comprehension at C1") == "LC"

    def test_vocab_alias(self):
        assert extract_category("vocabulary performance") == "Vocab"

    def test_total_alias(self):
        assert extract_category("overall total results") == "Total"

    def test_no_cat_returns_none(self):
        assert extract_category("What is the best model?") is None


# ── extract_licensing ─────────────────────────────────────────────────────────

class TestExtractLicensing:
    def test_open_source(self):
        assert extract_licensing("show open-source models") == "Open_Source"

    def test_proprietary(self):
        assert extract_licensing("only proprietary models") == "Proprietary"

    def test_closed_source(self):
        assert extract_licensing("closed-source LLMs only") == "Proprietary"

    def test_no_licensing(self):
        assert extract_licensing("top 5 models at B2") is None


# ── extract_top_n ─────────────────────────────────────────────────────────────

class TestExtractTopN:
    def test_top_keyword(self):
        assert extract_top_n("top 10 models") == 10

    def test_bottom_keyword(self):
        assert extract_top_n("bottom 3 models") == 3

    def test_bare_number(self):
        assert extract_top_n("give me 7 results") == 7

    def test_default_on_no_number(self):
        assert extract_top_n("show me models", default=5) == 5

    def test_capped_at_25(self):
        assert extract_top_n("top 100 models") == 25


# ── extract_ascending ─────────────────────────────────────────────────────────

class TestExtractAscending:
    def test_worst(self):
        assert extract_ascending("show worst performers") is True

    def test_lowest(self):
        assert extract_ascending("lowest scores at B2") is True

    def test_top_is_not_ascending(self):
        assert extract_ascending("top 5 models") is False

    def test_best_is_not_ascending(self):
        assert extract_ascending("best models for C1") is False


# ── resolve_model_name ────────────────────────────────────────────────────────

_DB_NAMES = [
    "GPT-6 Astra",
    "GPT-6 Luna",
    "Llama 3.1 - 70B",
    "Llama 3.1 - 8B",
    "Qwen 2 - 0.5B",
    "Qwen 2 - 1.5B",
    "Qwen 2.5 - 7B",
    "Gemma 3 - 12B",
    "Gemma 3 - 27B",
    "Mistral - 7B",
]


class TestResolveModelName:
    def test_exact_case_insensitive(self):
        result = resolve_model_name("gpt-6 astra score", _DB_NAMES)
        assert result == ["GPT-6 Astra"]

    def test_disambiguates_size_variants(self):
        # "70B" should uniquely resolve to the 70B variant
        result = resolve_model_name("Llama 3.1 - 70B grammar", _DB_NAMES)
        assert result == ["Llama 3.1 - 70B"]

    def test_disambiguates_version_variants(self):
        result = resolve_model_name("Qwen 2.5 - 7B score", _DB_NAMES)
        assert result == ["Qwen 2.5 - 7B"]

    def test_ambiguous_returns_multiple(self):
        # "Gemma 3" matches both 12B and 27B — should return both
        result = resolve_model_name("Gemma 3 performance at B2", _DB_NAMES)
        assert len(result) >= 2
        assert "Gemma 3 - 12B" in result
        assert "Gemma 3 - 27B" in result

    def test_empty_query_returns_empty(self):
        result = resolve_model_name("", _DB_NAMES)
        assert result == []

    def test_empty_names_returns_empty(self):
        result = resolve_model_name("GPT-6 Astra score", [])
        assert result == []

    def test_no_match_returns_empty(self):
        result = resolve_model_name("Claude 3.5 Sonnet", _DB_NAMES)
        assert result == []

    def test_does_not_equate_qwen2_and_qwen25(self):
        # "Qwen 2 - 0.5B" must not be returned when asking for "Qwen 2.5"
        result = resolve_model_name("Qwen 2.5 best score", _DB_NAMES)
        assert "Qwen 2 - 0.5B" not in result
        assert "Qwen 2 - 1.5B" not in result
