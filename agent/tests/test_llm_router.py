"""
Tests for agent/llm/router.py — all LLM calls are mocked.

Run from leaderboard/agent/:
    python -m pytest tests/test_llm_router.py -v
"""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import MagicMock

from llm.router import classify_with_llm, ALLOWED_INTENTS, _validate

_ALL_MODELS = ["GPT-6 Astra", "Llama 3.1 - 70B", "Qwen 2.5 - 7B", "Gemma 3 - 12B"]


def _llm_returning(text: str):
    """Return a mock LLM whose predict() returns `text`."""
    llm = MagicMock()
    llm.predict.return_value = text
    return llm


# ── classify_with_llm ─────────────────────────────────────────────────────────

class TestClassifyWithLlm:
    def test_returns_none_when_llm_is_none(self):
        result = classify_with_llm(None, "some message", None, [], _ALL_MODELS)
        assert result is None

    def test_happy_path(self):
        payload = json.dumps({
            "intent": "lookup_score",
            "models": ["GPT-6 Astra"],
            "cefr_level": "B2",
            "category": "Grammar",
            "top_n": None,
            "ascending": False,
            "needs_clarification": False,
        })
        llm = _llm_returning(payload)
        result = classify_with_llm(llm, "GPT-6 Astra B2 grammar", "lookup_score", _ALL_MODELS, _ALL_MODELS)
        assert result is not None
        assert result["intent"] == "lookup_score"
        assert result["models"] == ["GPT-6 Astra"]
        assert result["cefr_level"] == "B2"
        assert result["category"] == "Grammar"

    def test_strips_markdown_fences(self):
        payload = "```json\n" + json.dumps({
            "intent": "rank_models",
            "models": [],
            "cefr_level": "C1",
            "category": "Total",
            "top_n": 5,
            "ascending": False,
            "needs_clarification": False,
        }) + "\n```"
        llm = _llm_returning(payload)
        result = classify_with_llm(llm, "top 5 at C1", "rank_models", [], _ALL_MODELS)
        assert result is not None
        assert result["intent"] == "rank_models"

    def test_returns_none_on_invalid_json(self):
        llm = _llm_returning("not valid json at all")
        result = classify_with_llm(llm, "anything", None, [], _ALL_MODELS)
        assert result is None

    def test_returns_none_when_predict_raises(self):
        llm = MagicMock()
        llm.predict.side_effect = RuntimeError("network error")
        result = classify_with_llm(llm, "anything", None, [], _ALL_MODELS)
        assert result is None


# ── _validate ─────────────────────────────────────────────────────────────────

class TestValidate:
    def _base(self, **kwargs):
        base = {
            "intent": "lookup_score",
            "models": [],
            "cefr_level": None,
            "category": None,
            "top_n": None,
            "ascending": False,
            "needs_clarification": False,
        }
        base.update(kwargs)
        return base

    def test_valid_returns_dict(self):
        result = _validate(self._base(), _ALL_MODELS)
        assert result is not None
        assert result["intent"] == "lookup_score"

    def test_invalid_intent_rejected(self):
        result = _validate(self._base(intent="drop_table"), _ALL_MODELS)
        assert result is None

    def test_invalid_cefr_rejected(self):
        result = _validate(self._base(cefr_level="D1"), _ALL_MODELS)
        assert result is None

    def test_invalid_category_rejected(self):
        result = _validate(self._base(category="Pronunciation"), _ALL_MODELS)
        assert result is None

    def test_invented_model_name_rejected(self):
        result = _validate(self._base(models=["FakeModel - 99B"]), _ALL_MODELS)
        assert result is not None
        assert "FakeModel - 99B" not in result["models"]
        assert result["models"] == []

    def test_model_name_normalised_to_canonical_case(self):
        result = _validate(self._base(models=["gpt-6 astra"]), _ALL_MODELS)
        assert result is not None
        assert result["models"] == ["GPT-6 Astra"]

    def test_top_n_clamped(self):
        result = _validate(self._base(top_n=999), _ALL_MODELS)
        assert result is not None
        assert result["top_n"] == 5  # out-of-range → default 5

    def test_top_n_valid(self):
        result = _validate(self._base(top_n=10), _ALL_MODELS)
        assert result is not None
        assert result["top_n"] == 10

    def test_all_intents_allowed(self):
        for intent in ALLOWED_INTENTS:
            result = _validate(self._base(intent=intent), _ALL_MODELS)
            assert result is not None, f"Intent {intent!r} was unexpectedly rejected"

    def test_not_a_dict_returns_none(self):
        assert _validate(["lookup_score"], _ALL_MODELS) is None
        assert _validate(None, _ALL_MODELS) is None

    def test_model_mention_passes_through(self):
        """model_mention is free-text; it passes through even if not in catalog."""
        result = _validate(self._base(model_mention="FooBar 9000"), _ALL_MODELS)
        assert result is not None
        assert result["model_mention"] == "FooBar 9000"

    def test_model_mention_none_when_absent(self):
        result = _validate(self._base(), _ALL_MODELS)
        assert result is not None
        assert result["model_mention"] is None

    def test_licensing_open_source_accepted(self):
        result = _validate(self._base(licensing="Open_Source"), _ALL_MODELS)
        assert result is not None
        assert result["licensing"] == "Open_Source"

    def test_licensing_proprietary_accepted(self):
        result = _validate(self._base(licensing="Proprietary"), _ALL_MODELS)
        assert result is not None
        assert result["licensing"] == "Proprietary"

    def test_licensing_invalid_dropped(self):
        result = _validate(self._base(licensing="MIT"), _ALL_MODELS)
        assert result is not None
        assert result["licensing"] is None


# ── Intent decoupling (Phase 2B regression guard) ─────────────────────────────

class TestIntentDecoupling:
    """Guard against the E0 regression: intent must NOT depend on model availability."""

    def _llm_with_route(self, intent: str, models: list, model_mention: str = None,
                        needs_clarification: bool = False):
        """Mock LLM that returns a JSON route with the given intent/models."""
        payload = json.dumps({
            "intent": intent,
            "models": models,
            "model_mention": model_mention,
            "cefr_level": "B2",
            "category": "Grammar",
            "top_n": None,
            "ascending": False,
            "licensing": None,
            "needs_clarification": needs_clarification,
        })
        llm = MagicMock()
        llm.predict.return_value = payload
        return llm

    def test_lookup_score_preserved_when_model_not_in_candidates(self):
        """If the LLM correctly returns lookup_score, validation must not drop it."""
        llm = self._llm_with_route(
            intent="lookup_score",
            models=[],            # model not in candidate list
            model_mention="Llama 3.1 - 70B",
            needs_clarification=True,
        )
        # Candidates contain only GPT-6 Astra (simulates E0 alphabetical-first-10 bug)
        result = classify_with_llm(
            llm,
            "What is Llama 3.1 - 70B's B2 Grammar score?",
            "lookup_score",
            ["GPT-6 Astra"],   # Llama not in this list
            _ALL_MODELS,       # but Llama IS in full catalog
        )
        assert result is not None
        assert result["intent"] == "lookup_score", (
            "lookup_score intent must survive even when the model is absent from candidates"
        )
        assert result["model_mention"] == "Llama 3.1 - 70B"
        assert result["needs_clarification"] is True

    def test_compare_models_preserved_when_models_not_in_candidates(self):
        llm = self._llm_with_route(
            intent="compare_models",
            models=[],
            model_mention="Llama 3.1 - 70B",
            needs_clarification=True,
        )
        result = classify_with_llm(
            llm,
            "Compare Llama 3.1 - 70B and Gemma 3 - 12B at B2 Total",
            "compare_models",
            ["GPT-6 Astra"],
            _ALL_MODELS,
        )
        assert result is not None
        assert result["intent"] == "compare_models"


# ── retrieve_candidates ───────────────────────────────────────────────────────

class TestRetrieveCandidates:
    """retrieve_candidates must surface relevant models, not alphabetical first-N."""

    _CATALOG = [
        "Alfred",
        "Aya-23",
        "ChatGPT 4o",
        "ChatGPT 4o mini",
        "Claude 3.5 Sonnet",
        "DeepSeek-R1 - 671B",
        "Gemma 3 - 12B",
        "Gemma 3 - 27B",
        "GPT-6 Astra",
        "Llama 3.1 - 70B",
        "Llama 3.3 - 70B",
        "Mistral",
        "Phi 4",
        "Qwen 2 - 0.5B",
        "Qwen 2 - 7B",
        "Qwen 2.5 - 7B",
    ]

    def test_import(self):
        from intents.entity_utils import retrieve_candidates
        assert callable(retrieve_candidates)

    def test_surfaces_llama_variants(self):
        from intents.entity_utils import retrieve_candidates
        result = retrieve_candidates("llama 3.1 70b b2 grammar", self._CATALOG)
        assert "Llama 3.1 - 70B" in result, f"Expected Llama 3.1 - 70B in {result}"

    def test_surfaces_gemma_family(self):
        from intents.entity_utils import retrieve_candidates
        result = retrieve_candidates("gemma 3 27b c1 reading", self._CATALOG)
        assert "Gemma 3 - 27B" in result, f"Expected Gemma 3 - 27B in {result}"

    def test_surfaces_phi_from_phi4_query(self):
        from intents.entity_utils import retrieve_candidates
        result = retrieve_candidates("phi4 b1 vocab", self._CATALOG)
        assert "Phi 4" in result, f"Expected Phi 4 in {result}"

    def test_surfaces_mistral(self):
        from intents.entity_utils import retrieve_candidates
        result = retrieve_candidates("mistral b2 listening", self._CATALOG)
        assert "Mistral" in result, f"Expected Mistral in {result}"

    def test_does_not_exceed_limit(self):
        from intents.entity_utils import retrieve_candidates
        result = retrieve_candidates("llama qwen gemma phi mistral", self._CATALOG, limit=6)
        assert len(result) <= 6

    def test_empty_message_returns_empty(self):
        from intents.entity_utils import retrieve_candidates
        assert retrieve_candidates("", self._CATALOG) == []

    def test_deduplicates_results(self):
        from intents.entity_utils import retrieve_candidates
        result = retrieve_candidates("Llama 3.1 - 70B grammar", self._CATALOG)
        assert len(result) == len(set(result)), "Results contain duplicates"

    def test_exact_model_found(self):
        from intents.entity_utils import retrieve_candidates
        result = retrieve_candidates("GPT-6 Astra B2 Grammar", self._CATALOG)
        assert "GPT-6 Astra" in result, f"Expected GPT-6 Astra in {result}"

    def test_qwen_family_expansion(self):
        from intents.entity_utils import retrieve_candidates
        result = retrieve_candidates("qwen 2 0.5b A1 total", self._CATALOG)
        # Should find Qwen variants; Qwen 2 - 0.5B is an exact/near-exact match
        qwen_results = [r for r in result if r.startswith("Qwen")]
        assert qwen_results, f"Expected at least one Qwen model in {result}"
