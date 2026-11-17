"""
Tests for agent/llm/sanitize.py (input sanitization).

Run from leaderboard/agent/:
    python -m pytest tests/test_interpreter.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from llm.sanitize import sanitize, MAX_INPUT_LENGTH


class TestSanitizeBasic:
    def test_empty_string(self):
        assert sanitize('') == ''

    def test_non_string_returns_empty(self):
        assert sanitize(None) == ''    # type: ignore[arg-type]
        assert sanitize(123) == ''     # type: ignore[arg-type]

    def test_plain_ascii_unchanged(self):
        text = "What is the B2 Grammar score for GPT-6 Astra?"
        assert sanitize(text) == text

    def test_strips_leading_trailing_whitespace(self):
        assert sanitize("  hello  ") == "hello"

    def test_collapses_multiple_spaces(self):
        assert sanitize("a  b   c") == "a b c"

    def test_normalizes_tabs_to_space(self):
        assert sanitize("a\tb") == "a b"

    def test_normalizes_newlines_to_space(self):
        assert sanitize("line1\nline2") == "line1 line2"

    def test_strips_crlf(self):
        assert sanitize("line1\r\nline2") == "line1 line2"


class TestSanitizeUnicode:
    def test_nfc_normalization(self):
        # e + combining acute → é (NFC precomposed)
        nfd = "é"  # e + combining acute
        result = sanitize(nfd)
        assert result == "é"   # NFC é

    def test_non_breaking_space_normalized(self):
        assert sanitize("a\xa0b") == "a b"

    def test_zero_width_joiner_stripped(self):
        # Zero-width joiner U+200D is a Cf character
        assert '‍' not in sanitize("a‍b")

    def test_bom_stripped(self):
        assert '﻿' not in sanitize("﻿text")

    def test_ideographic_space_normalized(self):
        assert sanitize("a　b") == "a b"


class TestSanitizeModelTokens:
    """Verify that model-version discriminating tokens are preserved."""

    def test_preserves_decimal_version(self):
        result = sanitize("Qwen 2.5 B2 grammar")
        assert "2.5" in result

    def test_preserves_size_token_B(self):
        result = sanitize("Qwen 2 - 0.5B")
        assert "0.5B" in result or "0.5b" in result

    def test_preserves_large_size_token(self):
        result = sanitize("Llama 3.1 - 70B B2")
        assert "70B" in result or "70b" in result

    def test_preserves_dash_in_model_name(self):
        result = sanitize("GPT-6 Astra B2 grammar")
        assert "GPT-6" in result

    def test_preserves_version_number_after_space(self):
        result = sanitize("Phi 4 B1 vocab")
        assert "4" in result

    def test_preserves_size_with_decimal(self):
        result = sanitize("Qwen 3.5 - 0.8B c2 total")
        assert "3.5" in result
        assert "0.8B" in result or "0.8b" in result


class TestSanitizeLength:
    def test_short_message_unchanged_length(self):
        text = "Hello, what is B2?"
        assert len(sanitize(text)) == len(text)

    def test_long_message_truncated(self):
        long = "word " * 200   # 1000 chars
        result = sanitize(long)
        assert len(result) <= MAX_INPUT_LENGTH

    def test_truncation_at_word_boundary(self):
        # Construct a message that's slightly over the limit
        word = "a" * 10
        text = " ".join([word] * (MAX_INPUT_LENGTH // 11 + 2))
        result = sanitize(text)
        assert len(result) <= MAX_INPUT_LENGTH
        # Result should not end mid-word
        assert not result.endswith(" ")

    def test_exact_limit_not_truncated(self):
        text = "x" * MAX_INPUT_LENGTH
        result = sanitize(text)
        assert len(result) == MAX_INPUT_LENGTH


class TestSanitizeSecurity:
    """Verify that potentially harmful inputs are handled safely."""

    def test_sql_like_input_preserved_as_text(self):
        # We don't strip SQL — the DB layer parameterizes; LLM sees plain text
        text = "DROP TABLE model;"
        result = sanitize(text)
        assert result == text

    def test_html_angle_brackets_preserved(self):
        # Sanitize is text-only; escaping is downstream responsibility
        text = "<script>alert('xss')</script>"
        assert sanitize(text) == text

    def test_repeated_control_chars_stripped(self):
        text = "hello\x00\x01\x02world"
        result = sanitize(text)
        assert '\x00' not in result
        assert 'hello' in result
        assert 'world' in result

    def test_format_characters_stripped(self):
        # Soft hyphen U+00AD and various format chars
        text = "GPT­6 Astra"
        result = sanitize(text)
        assert '­' not in result
