"""
Tests for agent/intents/i18n.py

Run from leaderboard/agent/:
    python -m pytest tests/test_i18n.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from intents.i18n import t, _T, _ALLOWED_LANGS


# ── Coverage: all keys have all languages ────────────────────────────────────

class TestAllKeysAllLanguages:
    @pytest.mark.parametrize("key", list(_T.keys()))
    def test_key_has_english(self, key):
        assert "en" in _T[key], f"Missing English translation for key {key!r}"

    @pytest.mark.parametrize("key", list(_T.keys()))
    @pytest.mark.parametrize("lang", sorted(_ALLOWED_LANGS))
    def test_key_has_lang(self, key, lang):
        assert lang in _T[key], f"Missing {lang!r} translation for key {key!r}"


# ── t() function ──────────────────────────────────────────────────────────────

class TestT:
    def test_returns_english_for_en(self):
        result = t("out_of_scope", "en")
        assert "LëtzEval" in result

    def test_returns_german(self):
        result = t("out_of_scope", "de")
        assert "LëtzEval" in result
        assert result != t("out_of_scope", "en")

    def test_unknown_lang_falls_back_to_english(self):
        assert t("reset_all", "xx") == t("reset_all", "en")

    def test_interpolation(self):
        result = t("ask_model_name", "en", level="B2", cat="Grammar")
        assert "B2" in result
        assert "Grammar" in result

    def test_interpolation_german(self):
        result = t("ambiguous_model", "de", names="GPT-6 Astra, Llama")
        assert "GPT-6 Astra" in result
        assert "Llama" in result

    def test_missing_key_returns_bracket_placeholder(self):
        result = t("nonexistent_key_xyz", "en")
        assert result == "[nonexistent_key_xyz]"

    def test_bad_placeholder_falls_back_to_english(self):
        # Pass a key that doesn't match the template — should not raise
        result = t("score_not_found", "en", wrong_key="value")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_rank_no_results_with_license_suffix(self):
        result = t("rank_no_results", "en", level="B2", cat="Grammar", license_suffix=" (open source models)")
        assert "B2" in result
        assert "Grammar" in result
        assert "open source models" in result

    def test_rank_no_results_empty_suffix(self):
        result = t("rank_no_results", "en", level="C1", cat="Total", license_suffix="")
        assert "C1" in result
        assert result.endswith(".")

    def test_greeting_all_languages(self):
        for lang in _ALLOWED_LANGS:
            result = t("greeting", lang)
            assert "LëtzEval" in result, f"Greeting missing LëtzEval for lang={lang!r}"

    def test_error_all_languages(self):
        for lang in _ALLOWED_LANGS:
            result = t("error", lang)
            assert len(result) > 0, f"Empty error message for lang={lang!r}"
