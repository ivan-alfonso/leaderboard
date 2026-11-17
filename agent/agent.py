"""
LëtzEval BAF conversational assistant.

Run from the leaderboard/agent/ directory:
    /home/adhav/besser-demo/.venv/bin/python3 agent.py

Requires: BAF 4.5.0 + PyTorch (available in /home/adhav/besser-demo/.venv)
Config:   config.yaml  (copy config.example.yaml and adjust paths if needed)

Agent modes (LETZEVAL_AGENT_MODE):
    classical  (default) — BAF PyTorch intent classifier routes messages directly
                           to handler states; LLM used only as entity-extraction
                           fallback in lookup/compare handlers.
    llm        — All messages pass through an LLM interpretation state first.
                 The LLM extracts intent, model names, CEFR level and category;
                 its validated output is passed to the same handler states.
                 When the LLM is unavailable, falls back to the BAF-classified
                 intent + classical entity extraction.
"""
import json
import logging
import operator as _op
import os
import sys
import traceback

# LLM interpreter and multilingual support (optional; falls back to deterministic)
try:
    from llm.config import get_llm_provider
    from llm.router import classify_with_llm, ALLOWED_INTENTS
    from llm.sanitize import sanitize as _sanitize_input
    from llm.translate import translate_text as _translate_text
except ImportError:
    get_llm_provider = lambda agent=None: None  # noqa: E731
    classify_with_llm = lambda *a, **kw: None   # noqa: E731
    ALLOWED_INTENTS = frozenset()
    _sanitize_input = lambda s: s              # noqa: E731
    _translate_text = lambda *a, **kw: None    # noqa: E731

# Ensure the agent/ package is importable when run directly
sys.path.insert(0, os.path.dirname(__file__))

from baf.core.agent import Agent
from baf.core.session import Session
from baf.exceptions.logger import logger as baf_logger
from baf.nlp.intent_classifier.intent_classifier_configuration import (
    SimpleIntentClassifierConfiguration,
)

from db.safe_db import (
    compare_models,
    find_models,
    get_all_model_names,
    get_coverage_stats,
    get_model_count,
    get_model_families,
    lookup_all_cefr_totals,
    lookup_score,
    rank_models,
    CEFR_LEVELS,
    CATEGORIES,
    METRIC_IDS,
)
from intents.entity_utils import (
    extract_ascending,
    extract_cefr_level,
    extract_category,
    extract_licensing,
    extract_top_n,
    resolve_model_name,
    retrieve_candidates,
)
from intents.responses import (
    CEFR_EXPLANATION,
    LEADERBOARD_OVERVIEW,
    METHODOLOGY_OVERVIEW,
    METRIC_EXPLANATIONS,
    SCORE_INTERPRETATION,
)
from intents.i18n import t as _t

baf_logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# LETZEVAL_AGENT_MODE: 'classical' (default) | 'llm'
# AGENT_MODE = os.environ.get('LETZEVAL_AGENT_MODE', 'classical').lower().strip()
AGENT_MODE = os.environ.get('LETZEVAL_AGENT_MODE', 'llm')
if AGENT_MODE not in ('classical', 'llm'):
    logging.warning("Unknown LETZEVAL_AGENT_MODE=%r; defaulting to 'classical'.", AGENT_MODE)
    AGENT_MODE = 'classical'

logging.info("Agent mode: %s", AGENT_MODE)

# Debug telemetry (never exposed in production chat; no SQL leaked)
# Set LETZEVAL_DEBUG_TELEMETRY=1 and optionally LETZEVAL_TELEMETRY_FILE=path
# to append one JSONL record per LLM routing call to the given file.
_DEBUG_TELEMETRY: bool = os.environ.get('LETZEVAL_DEBUG_TELEMETRY', '').lower() in ('1', 'true')
_TELEMETRY_FILE: str = os.environ.get(
    'LETZEVAL_TELEMETRY_FILE',
    os.path.join(os.path.dirname(__file__), 'evaluation_results', 'telemetry.jsonl'),
)


def _write_telemetry(record: dict) -> None:
    """Append one JSONL record to the telemetry file (debug-only)."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(_TELEMETRY_FILE)), exist_ok=True)
        with open(_TELEMETRY_FILE, 'a', encoding='utf-8') as _tf:
            _tf.write(json.dumps(record, default=str) + '\n')
    except Exception as _te:
        logging.debug("Telemetry write failed: %s", _te)


# ---------------------------------------------------------------------------
# Training sentences (20 per intent, from intents_train.csv)
# ---------------------------------------------------------------------------

_TRAIN: dict[str, list[str]] = {
    "explain_leaderboard": [
        "Orient me to this page.",
        "Tell me about this site.",
        "What is the purpose of this page?",
        "I am new here. What does this page do?",
        "Give me the big picture of this project.",
        "What kind of resource is this leaderboard?",
        "Who is this comparison intended for?",
        "Why was this evaluation initiative created?",
        "Tell me about LëtzEval and why it matters.",
        "Explain the Luxembourgish LLM evaluation project.",
        "What can researchers use this page for?",
        "Can you introduce this evaluation platform?",
        "What does this project aim to achieve?",
        "Why are language models tested in Luxembourgish?",
        "What does the Luxembourgish LLM leaderboard show?",
        "Why should someone look at these results?",
        "How is this leaderboard useful for AI research?",
        "What information does this evaluation site provide?",
        "Walk me through what this page is for.",
        "Help me understand what this website does.",
    ],
    "explain_methodology": [
        "How were the models tested?",
        "Explain the evaluation methodology.",
        "How are the model scores calculated?",
        "What procedure was used to evaluate the LLMs?",
        "How does the evaluation process work?",
        "How were the test questions selected?",
        "What kind of questions were given to the language models?",
        "How are the answers graded?",
        "Were the test prompts standardized across systems?",
        "What determines a model's final evaluation score?",
        "Describe the grading protocol.",
        "How did you ensure the evaluations were consistent?",
        "Does the method report uncertainty or confidence?",
        "What was done to validate the assessment methodology?",
        "How were model responses assessed for correctness?",
        "Are the results based on multiple-choice questions?",
        "How was the Luxembourgish language test designed?",
        "What makes the evaluation methodology reliable?",
        "How were the different CEFR-level scores obtained?",
        "Can you walk me through the benchmark procedure?",
    ],
    "lookup_score": [
        "How did Model X score at B2?",
        "What is the C1 Grammar score for Model Y?",
        "What score did Model X achieve in Vocabulary?",
        "I need Model X's A2 score, not its position.",
        "What percentage did Model X get at A1?",
        "How well did Model Y perform at C2?",
        "Find the Listening Comprehension score of Model X.",
        "Give me the B1 evaluation result for Model X.",
        "Can you retrieve Model X's Grammar performance?",
        "What was Model Y's score in A2 Vocabulary?",
        "Tell me the percentage score for Model X at C1.",
        "What result did Model X achieve for C2 Reading Comprehension?",
        "Look up the B2 Grammar score of Model Y.",
        "Can you find the total score for Model X at A2?",
        "What was Model X's recorded B2 reading result?",
        "Find the grammar percentage reported for Model Y at B1.",
        "What did Model X get in C2 listening?",
        "Show me just one score: Model Y at A1 total.",
        "Give me the results for Model X at B2 Grammar.",
        "What score does this model get at C1 Total?",
        "Show the B2 Grammar result for this model.",
        "Get the C2 vocabulary score for this LLM.",
        "What is the A1 score for this language model?",
        "Give me results for this model.",
        "Get results for this LLM.",
        "Show results for this language model.",
        "What is Model X B2 score?",
        "What is Model Y C1 Grammar score?",
        "What is this model's B2 Grammar score?",
        "What is Model X's score at A1 Total?",
    ],
    "rank_models": [
        "Which model tops the leaderboard?",
        "Who tops the C1 reading test?",
        "Which LLM has the strongest overall score?",
        "Rank the models by their B2 performance.",
        "What are the three best models for Grammar?",
        "Which open-source models score highest at C1?",
        "List the ten highest-scoring language models.",
        "Who leads the rankings for Vocabulary?",
        "Which model has the highest C2 score?",
        "Show me the worst performers at A1.",
        "List the top five open-source LLMs for B1 Grammar.",
        "Sort the models from best to worst by C1 score.",
        "Which model ranks first in the B2 category?",
        "Identify the strongest models at advanced CEFR levels.",
        "Find the leaders among openly licensed systems.",
        "Who got the strongest B2 vocabulary score?",
        "Which models achieved the highest scores in C2 reading?",
        "List the best closed-source models for Vocabulary.",
        "Show a leaderboard ordered by grammar accuracy.",
        "Bottom three models for C2 please.",
        "Show the top 5 models for C1 Total.",
        "Rank models by Macro Average.",
        "Who scores highest overall?",
    ],
    "compare_models": [
        "Compare Model X with Model Y.",
        "Which performs better, Model X or Model Y?",
        "How do Model X and Model Y differ at B2?",
        "Compare the Grammar scores of Model X and Model Y.",
        "Which of these two models performs better in Vocabulary?",
        "Show the performance differences between Model X and Model Y.",
        "How does Model X compare with Model Y across CEFR levels?",
        "Compare these three language models on Listening Comprehension.",
        "Is Model X stronger than Model Y on advanced language tasks?",
        "What is the score difference between Model X and Model Y at C1?",
        "Show a head-to-head for Model X and Model Y at A2.",
        "Which of the selected models performs better in Reading Comprehension?",
        "Show a side-by-side evaluation of Model X and Model Y.",
        "How much better is Model X than Model Y at B1?",
        "How large is the reading gap between these two models?",
        "What are the strengths of Model X relative to Model Y?",
        "Compare the scores of Model X and Model Y in every category.",
        "Where does Model Y beat Model X?",
        "Put three chosen models side by side.",
        "Contrast the two selected models on grammar.",
        "Compare this model with that one at C2.",
        "Compare these two models at C2 Grammar.",
        "How does this LLM compare with the other at B2?",
        "Put these LLMs side by side at C1.",
    ],
    "filter_results": [
        "Apply a filter for open-source models only.",
        "Restrict what is visible to proprietary models.",
        "Filter the leaderboard to B1 Vocabulary.",
        "Narrow this page to C1 results.",
        "Set the graph to A2 listening only.",
        "I only want to see Listening Comprehension scores.",
        "Exclude proprietary language models from the display.",
        "Set the CEFR filter to C1.",
        "Restrict the table to open-source models at B2.",
        "Apply the selected model family filter.",
        "Change the category filter to Vocabulary.",
        "Update the chart to show only C2 Grammar.",
        "Filter out models scoring below fifty percent.",
        "Hide everything below sixty percent.",
        "Show just the models from one specific family.",
        "Limit the displayed models to one model family.",
        "Apply a filter for the A1 level.",
        "Filter the chart to Grammar results.",
        "Keep only models meeting the selected performance threshold.",
        "Narrow the view to a specific model family.",
    ],
    "explain_metric": [
        "What does CEFR stand for?",
        "Define Listening Comprehension.",
        "Explain the A1 language proficiency level.",
        "What does C2 represent in language assessment?",
        "What is meant by Vocabulary in this benchmark?",
        "Describe the Grammar evaluation category.",
        "What does Reading Comprehension measure?",
        "What is the difference between A1 and B1?",
        "How is accuracy defined in language assessment?",
        "How should I interpret a score of 80 percent?",
        "What does the B2 label signify?",
        "What does an A2 label mean?",
        "Explain the different CEFR language levels.",
        "What does the Total metric mean?",
        "What skills are associated with the C1 level?",
        "Define the Listening Comprehension metric.",
        "What is measured in the Reading Comprehension category?",
        "What do the letters RC stand for here?",
        "How is accuracy different from language fluency?",
        "Interpret these percent-correct values for me.",
    ],
    "data_coverage": [
        "How many models are included in the leaderboard?",
        "What is the current number of listed LLMs?",
        "How many LLMs are in the evaluation dataset?",
        "What CEFR levels are covered by the evaluation?",
        "Which language assessment categories are available?",
        "Which language model families are represented?",
        "What information is stored for each evaluated model?",
        "Are all CEFR levels from A1 to C2 included?",
        "What dimensions exist in the evaluation dataset?",
        "Does Model X appear in the current dataset?",
        "Which levels have benchmark columns?",
        "How much information is exposed for each row?",
        "Is Model X included in the leaderboard?",
        "What is the scope of the available evaluation data?",
        "What models are available in the database?",
        "Can you list the model families in the evaluation dataset?",
        "Are parameter sizes available for the evaluated models?",
        "Which benchmarks are represented here?",
        "How many categories does the benchmark contain?",
        "What data fields are recorded per model?",
    ],
    "reset_view": [
        "Clear all active filters.",
        "Undo the filtering changes.",
        "Remove all filter restrictions.",
        "Reset the leaderboard to its default state.",
        "Restore the original unfiltered view.",
        "Cancel my previous filter selections.",
        "Remove the open-source filter.",
        "Clear the selected performance threshold.",
        "Return the chart to its initial state.",
        "Restore the default filtering settings.",
        "Reset the CEFR and category selections.",
        "Undo every view restriction.",
        "Remove all the applied filters.",
        "Reset the results display to normal.",
        "Go back to the default table view.",
        "Remove the B2 Grammar filter.",
        "Start over with the leaderboard filters.",
        "Put the table back to how it was.",
        "I want the original default graph again.",
        "Take off the reading filter only.",
    ],
    "out_of_scope": [
        "What is the weather tomorrow?",
        "Plan my holiday itinerary.",
        "Write me a poem about Luxembourg.",
        "What is the capital of France?",
        "How do I book a flight?",
        "Tell me a joke.",
        "Who won the football match yesterday?",
        "Debug an unrelated JavaScript library for me.",
        "What is the current Bitcoin price?",
        "Help me solve a mathematics homework problem.",
        "How do I cook risotto?",
        "Recommend a restaurant in Luxembourg City.",
        "How do I renew my passport?",
        "Generate a marketing slogan for my shop.",
        "Give me a recipe for chocolate cake.",
        "What are the best tourist attractions in Paris?",
        "Can you write a cover letter for a job?",
        "Translate this essay from French to German.",
        "What time is it in Tokyo?",
        "How do I practice a conversation in French?",
    ],
}

# ---------------------------------------------------------------------------
# Agent setup
# ---------------------------------------------------------------------------

agent = Agent("letzeval_assistant")
agent.load_properties(os.path.join(os.path.dirname(__file__), "config.yaml"))
websocket_platform = agent.use_websocket_platform(use_ui=False)

ic_config = SimpleIntentClassifierConfiguration(
    framework="pytorch",
    num_epochs=500,
    embedding_dim=64,
    hidden_dim=64,
    input_max_num_tokens=20,
    discard_oov_sentences=False,
    check_exact_prediction_match=True,
    activation_last_layer="softmax",
    lr=0.001,
)
agent.set_default_ic_config(ic_config)

# ---------------------------------------------------------------------------
# Intents
# ---------------------------------------------------------------------------

explain_leaderboard_intent = agent.new_intent("explain_leaderboard", _TRAIN["explain_leaderboard"])
explain_methodology_intent = agent.new_intent("explain_methodology", _TRAIN["explain_methodology"])
lookup_score_intent        = agent.new_intent("lookup_score",        _TRAIN["lookup_score"])
rank_models_intent         = agent.new_intent("rank_models",         _TRAIN["rank_models"])
compare_models_intent      = agent.new_intent("compare_models",      _TRAIN["compare_models"])
filter_results_intent      = agent.new_intent("filter_results",      _TRAIN["filter_results"])
explain_metric_intent      = agent.new_intent("explain_metric",      _TRAIN["explain_metric"])
data_coverage_intent       = agent.new_intent("data_coverage",       _TRAIN["data_coverage"])
reset_view_intent          = agent.new_intent("reset_view",          _TRAIN["reset_view"])
out_of_scope_intent        = agent.new_intent("out_of_scope",        _TRAIN["out_of_scope"])

# ---------------------------------------------------------------------------
# States
# ---------------------------------------------------------------------------

initial_state             = agent.new_state("initial_state",             initial=True)
explain_leaderboard_state = agent.new_state("explain_leaderboard_state")
explain_methodology_state = agent.new_state("explain_methodology_state")
lookup_score_state        = agent.new_state("lookup_score_state")
rank_models_state         = agent.new_state("rank_models_state")
compare_models_state      = agent.new_state("compare_models_state")
filter_results_state      = agent.new_state("filter_results_state")
explain_metric_state      = agent.new_state("explain_metric_state")
data_coverage_state       = agent.new_state("data_coverage_state")
reset_view_state          = agent.new_state("reset_view_state")
out_of_scope_state        = agent.new_state("out_of_scope_state")

# ---------------------------------------------------------------------------
# LLM provider (none by default; set LETZEVAL_LLM_PROVIDER env var to enable)
# ---------------------------------------------------------------------------

_llm = get_llm_provider(agent)

# ---------------------------------------------------------------------------
# Cached model names (loaded once at startup, used in every SQL state)
# ---------------------------------------------------------------------------

_ALL_MODEL_NAMES: list[str] = []


def _get_all_names() -> list[str]:
    global _ALL_MODEL_NAMES
    if not _ALL_MODEL_NAMES:
        _ALL_MODEL_NAMES = get_all_model_names()
    return _ALL_MODEL_NAMES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_user_message(session: Session) -> str:
    """Return the user's text from the current session event, or '' if unavailable."""
    event = session.event
    if event is None:
        return ""
    msg = getattr(event, "message", None)
    return msg if isinstance(msg, str) else ""


def _lang(session: Session) -> str:
    """Return the validated UI language for this session (default: 'en')."""
    lang = session.get('ui_language') or 'en'
    return lang if lang in ('en', 'de', 'fr', 'it', 'lb', 'pt') else 'en'


def _reply(session: Session, text: str) -> None:
    """Send a reply, translating to the session language when it is not English.

    Used for English-only dynamic responses (scores, rankings, explanations).
    Static messages that already go through _t() use session.reply() directly.
    Falls back to the original English text when the LLM is unavailable.
    """
    lang = _lang(session)
    if lang == 'en' or _llm is None:
        session.reply(text)
        return
    translated = _translate_text(_llm, text, lang)
    session.reply(translated if translated else text)


def _send_ui_action(session: Session, ui_action: dict) -> None:
    """Encode a UI action as a sentinel-prefixed text message."""
    session.reply(f'__UI_ACTION__{json.dumps(ui_action)}')


def _consume_llm_route(session: Session) -> dict | None:
    """Read and clear the LLM-provided route stored in the session.

    Returns the parsed route dict, or None if not present.
    Handler state bodies call this once at the start; in classical mode
    the key is never set so this always returns None.
    """
    val = session.get('_llm_route')
    if val:
        session.set('_llm_route', None)
        session.set('_next', None)
        try:
            return json.loads(val)
        except Exception:
            return None
    return None


def _reply_options_if_ambiguous(
    session: Session,
    candidates: list[str],
    pending_intent: str,
    pending_cefr: str | None = None,
    pending_cat: str | None = None,
    pending_top_n: int | None = None,
    pending_ascending: bool = False,
) -> bool:
    """If there are multiple candidates, send clickable options and store pending intent.

    Returns True if clarification was sent (caller should return early).
    Returns False if candidates is empty or exactly one (no clarification needed).
    """
    if len(candidates) <= 1:
        return False
    session.set('_pending_route', json.dumps({
        'intent': pending_intent,
        'models': [],
        'cefr_level': pending_cefr,
        'category': pending_cat,
        'top_n': pending_top_n,
        'ascending': pending_ascending,
        'needs_clarification': True,
    }))
    websocket_platform.reply_options(session, candidates[:5])
    return True


# ---------------------------------------------------------------------------
# Transitions: set up based on AGENT_MODE
# ---------------------------------------------------------------------------

_ALL_INTENTS = [
    explain_leaderboard_intent, explain_methodology_intent,
    lookup_score_intent, rank_models_intent, compare_models_intent,
    filter_results_intent, explain_metric_intent, data_coverage_intent,
    reset_view_intent, out_of_scope_intent,
]

if AGENT_MODE == 'llm':
    # LLM mode: all messages route through the interpretation state first
    llm_interpret_state = agent.new_state("llm_interpret_state")

    for intent_obj in _ALL_INTENTS:
        initial_state.when_intent_matched(intent_obj).go_to(llm_interpret_state)
    initial_state.when_no_intent_matched().go_to(llm_interpret_state)

    # Variable-based transitions: llm_interpret_state → handler states
    _INTENT_STATE_MAP = {
        'explain_leaderboard': explain_leaderboard_state,
        'explain_methodology': explain_methodology_state,
        'lookup_score':        lookup_score_state,
        'rank_models':         rank_models_state,
        'compare_models':      compare_models_state,
        'filter_results':      filter_results_state,
        'explain_metric':      explain_metric_state,
        'data_coverage':       data_coverage_state,
        'reset_view':          reset_view_state,
        'out_of_scope':        out_of_scope_state,
        'clarify':             initial_state,   # pending clarification → wait
    }
    for intent_name, state_obj in _INTENT_STATE_MAP.items():
        llm_interpret_state.when_variable_matches_operation(
            '_next', _op.eq, intent_name
        ).go_to(state_obj)
    llm_interpret_state.go_to(out_of_scope_state)   # fallback if _next not set

else:
    # Classical mode: direct routing
    initial_state.when_intent_matched(explain_leaderboard_intent).go_to(explain_leaderboard_state)
    initial_state.when_intent_matched(explain_methodology_intent).go_to(explain_methodology_state)
    initial_state.when_intent_matched(lookup_score_intent).go_to(lookup_score_state)
    initial_state.when_intent_matched(rank_models_intent).go_to(rank_models_state)
    initial_state.when_intent_matched(compare_models_intent).go_to(compare_models_state)
    initial_state.when_intent_matched(filter_results_intent).go_to(filter_results_state)
    initial_state.when_intent_matched(explain_metric_intent).go_to(explain_metric_state)
    initial_state.when_intent_matched(data_coverage_intent).go_to(data_coverage_state)
    initial_state.when_intent_matched(reset_view_intent).go_to(reset_view_state)
    initial_state.when_intent_matched(out_of_scope_intent).go_to(out_of_scope_state)
    initial_state.when_no_intent_matched().go_to(out_of_scope_state)

# All handler states return to initial_state
for _s in [
    explain_leaderboard_state, explain_methodology_state,
    lookup_score_state, rank_models_state, compare_models_state,
    filter_results_state, explain_metric_state, data_coverage_state,
    reset_view_state, out_of_scope_state,
]:
    _s.go_to(initial_state)

# ---------------------------------------------------------------------------
# State body functions
# ---------------------------------------------------------------------------

def initial_body(session: Session) -> None:
    if not session.get("greeted"):
        session.set("greeted", True)
        session.reply(_t('greeting', _lang(session)))


initial_state.set_body(initial_body)


# ── LLM mode: interpret state ────────────────────────────────────────────────

def llm_interpret_body(session: Session) -> None:
    """Run the LLM interpreter and store route + next-state in session."""
    msg = _get_user_message(session)
    lang = _lang(session)
    all_names = _get_all_names()

    # Resolve pending clarification: user responded to reply_options
    pending_json = session.get('_pending_route')
    if pending_json:
        session.set('_pending_route', None)
        try:
            pending = json.loads(pending_json)
            # Check if user's message resolves to a known model
            matches = resolve_model_name(msg, all_names)
            # Also check exact match (user typed the model name precisely)
            exact = next((n for n in all_names if n.lower() == msg.strip().lower()), None)
            chosen = [exact] if exact else (matches[:1] if matches else [])
            if chosen:
                pending['models'] = chosen
                pending['needs_clarification'] = False
                session.set('_llm_route', json.dumps(pending))
                session.set('_next', pending.get('intent', 'out_of_scope'))
                return
        except Exception:
            pass
        # Pending resolution failed — fall through to normal LLM routing

    # LLM unavailable — fall back to BAF classifier intent + classical extraction
    if _llm is None:
        try:
            baf_intent = session.event.predicted_intent.intent.name
        except AttributeError:
            baf_intent = 'out_of_scope'
        session.set('_next', baf_intent if baf_intent in _INTENT_STATE_MAP else 'out_of_scope')
        return

    # Sanitize and route via LLM
    sanitized = _sanitize_input(msg)

    # Build a query-aware candidate shortlist (never an arbitrary alphabetical first-N)
    candidates = retrieve_candidates(sanitized, all_names)

    # Optional debug telemetry (LETZEVAL_DEBUG_TELEMETRY=1 to enable)
    capture: dict = {} if _DEBUG_TELEMETRY else None  # type: ignore[assignment]
    if capture is not None:
        capture['case_id'] = session.get('_eval_case_id')
        capture['input'] = msg
        capture['sanitized'] = sanitized
        capture['candidates'] = candidates
        capture['llm_invocations'] = 1

    route = classify_with_llm(_llm, sanitized, None, candidates, all_names, _capture=capture)

    if capture is not None:
        capture['route'] = route
        capture['_next'] = route.get('intent', 'out_of_scope') if route else None
        _write_telemetry(capture)

    if route is None:
        # LLM call failed — recover BAF classifier intent as fallback
        try:
            baf_intent = session.event.predicted_intent.intent.name
        except AttributeError:
            baf_intent = 'out_of_scope'
        session.set('_next', baf_intent if baf_intent in _INTENT_STATE_MAP else 'out_of_scope')
        return

    # Ambiguous model — show clickable options and wait for selection
    if route.get('needs_clarification') and route.get('models'):
        candidates = route['models']
        session.set('_pending_route', json.dumps({
            'intent': route.get('intent', 'lookup_score'),
            'models': [],
            'cefr_level': route.get('cefr_level'),
            'category': route.get('category'),
            'top_n': route.get('top_n'),
            'ascending': route.get('ascending', False),
            'needs_clarification': True,
        }))
        session.reply(_t('llm_needs_clarification', lang))
        websocket_platform.reply_options(session, candidates)
        session.set('_next', 'clarify')
        return

    session.set('_llm_route', json.dumps(route))
    session.set('_next', route.get('intent', 'out_of_scope'))


if AGENT_MODE == 'llm':
    llm_interpret_state.set_body(llm_interpret_body)


# ── Explain states ────────────────────────────────────────────────────────────

def explain_leaderboard_body(session: Session) -> None:
    _consume_llm_route(session)
    _reply(session, LEADERBOARD_OVERVIEW)


explain_leaderboard_state.set_body(explain_leaderboard_body)


def explain_methodology_body(session: Session) -> None:
    _consume_llm_route(session)
    _reply(session, METHODOLOGY_OVERVIEW)


explain_methodology_state.set_body(explain_methodology_body)


def explain_metric_body(session: Session) -> None:
    route = _consume_llm_route(session)
    try:
        msg = _get_user_message(session)
        cat = route['category'] if route and route.get('category') else extract_category(msg)
        lower = msg.lower()
        if "cefr" in lower or "level" in lower or any(lv.lower() in lower for lv in ("a1", "a2", "b1", "b2", "c1", "c2")):
            level_reply = CEFR_EXPLANATION
            if cat and cat in METRIC_EXPLANATIONS:
                level_reply += f"\n\n{METRIC_EXPLANATIONS[cat]}"
            _reply(session, level_reply)
        elif cat and cat in METRIC_EXPLANATIONS:
            _reply(session, METRIC_EXPLANATIONS[cat])
        elif "percent" in lower or "score" in lower or "interpret" in lower:
            _reply(session, SCORE_INTERPRETATION)
        elif "macro" in lower or "overall" in lower or "average" in lower:
            _reply(session, METRIC_EXPLANATIONS["Macro"])
        else:
            _reply(session, CEFR_EXPLANATION)
    except Exception:
        baf_logger.error("explain_metric_body failed:\n%s", traceback.format_exc())
        session.reply(_t('error', _lang(session)))


explain_metric_state.set_body(explain_metric_body)


# ── Lookup score ──────────────────────────────────────────────────────────────

def lookup_score_body(session: Session) -> None:
    try:
        msg = _get_user_message(session)
        lang = _lang(session)
        all_names = _get_all_names()

        route = _consume_llm_route(session)
        if route:
            level      = route.get('cefr_level')
            cat        = route.get('category')
            candidates = route.get('models', [])
        else:
            level      = extract_cefr_level(msg)
            cat        = extract_category(msg)
            candidates = resolve_model_name(msg, all_names)

            # Classical LLM fallback when entity extraction is uncertain
            if _llm and not candidates:
                fb = classify_with_llm(_llm, msg, 'lookup_score', candidates, all_names)
                if fb:
                    if fb.get('models'):
                        candidates = fb['models']
                    if not level and fb.get('cefr_level'):
                        level = fb['cefr_level']
                    if not cat and fb.get('category'):
                        cat = fb['category']
                    if fb.get('needs_clarification'):
                        session.reply(_t('llm_needs_clarification', lang))
                        return

        # Clickable options when still ambiguous (works in both modes)
        if len(candidates) > 1:
            sent = _reply_options_if_ambiguous(
                session, candidates,
                pending_intent='lookup_score',
                pending_cefr=level, pending_cat=cat,
            )
            if sent:
                return

        # Handle "macro avg" / "overall" queries (no level needed)
        if not level and ("macro" in msg.lower() or ("overall" in msg.lower() and not cat)):
            if not candidates:
                session.reply(_t('ask_model_macro', lang))
                return
            result = lookup_score(candidates[0], "All", "Macro")
            if result:
                _reply(session,
                    f"**{result['model_name']}** — Macro Average: **{float(result['value']):.2f}%**"
                )
            else:
                _reply(session, f"I couldn't find a Macro Average score for *{candidates[0]}*.")
            return

        # No level specified: show all CEFR Totals when the model is identifiable
        if not level:
            if not candidates:
                session.reply(_t('ask_model_name', lang, level='', cat='CEFR Totals'))
                return
            rows = lookup_all_cefr_totals(candidates[0])
            if not rows:
                session.reply(_t('cefr_totals_not_found', lang, model=candidates[0]))
                return
            header = f"**{rows[0]['model_name']} — CEFR Totals**\n\n"
            lines = [f"• **{r['metric_name']}**: {r['score']:.2f}%" for r in rows]
            _reply(session, header + "\n".join(lines))
            return

        # Default category to Total if not specified
        if not cat:
            cat = "Total"

        # Clarification: missing model name
        if not candidates:
            session.reply(_t('ask_model_name', lang, level=level, cat=cat))
            return

        result = lookup_score(candidates[0], level, cat)
        if result:
            _reply(session,
                f"**{result['model_name']}** — {result['metric_name']}: **{float(result['value']):.2f}%**"
            )
        else:
            session.reply(_t('score_not_found', lang, level=level, cat=cat, model=candidates[0]))
    except Exception:
        baf_logger.error("lookup_score_body failed:\n%s", traceback.format_exc())
        session.reply(_t('error', _lang(session)))


lookup_score_state.set_body(lookup_score_body)


# ── Rank models ───────────────────────────────────────────────────────────────

def rank_models_body(session: Session) -> None:
    try:
        msg = _get_user_message(session)
        lang = _lang(session)

        route = _consume_llm_route(session)
        if route:
            level     = route.get('cefr_level') or 'All'
            cat       = route.get('category') or ('Macro' if level == 'All' else 'Total')
            top_n     = route.get('top_n') or 5
            ascending = bool(route.get('ascending', False))
            # Use LLM-extracted licensing first; fall back to entity extraction from raw text
            licensing = route.get('licensing') or extract_licensing(msg)
        else:
            level = extract_cefr_level(msg)
            cat   = extract_category(msg)
            top_n = extract_top_n(msg, default=5)
            ascending = extract_ascending(msg)
            licensing = extract_licensing(msg)

            if not level:
                level = "All"
            if not cat:
                cat = "Macro" if level == "All" else "Total"

        rows = rank_models(level, cat, top_n=top_n, ascending=ascending, licensing=licensing)

        if not rows:
            license_suffix = f" ({licensing.replace('_', ' ')} models)" if licensing else ""
            session.reply(_t('rank_no_results', lang, level=level, cat=cat, license_suffix=license_suffix))
            return

        direction = "Lowest" if ascending else "Top"
        header = (
            f"**{direction} {len(rows)} — {level} {cat}**"
            + (f" · {licensing.replace('_', ' ')}" if licensing else "")
            + "\n\n"
        )
        lines = [
            f"{i+1}. **{r['model_name']}** — {r['score']:.2f}%"
            for i, r in enumerate(rows)
        ]
        _reply(session, header + "\n".join(lines))
    except Exception:
        baf_logger.error("rank_models_body failed:\n%s", traceback.format_exc())
        session.reply(_t('error', _lang(session)))


rank_models_state.set_body(rank_models_body)


# ── Compare models ────────────────────────────────────────────────────────────

def compare_models_body(session: Session) -> None:
    try:
        msg = _get_user_message(session)
        lang = _lang(session)
        all_names = _get_all_names()

        route = _consume_llm_route(session)
        if route:
            level      = route.get('cefr_level')
            cat        = route.get('category')
            candidates = route.get('models', [])
        else:
            level      = extract_cefr_level(msg)
            cat        = extract_category(msg)
            candidates = resolve_model_name(msg, all_names)

            # Classical LLM fallback when fewer than 2 candidates found
            if _llm and len(candidates) < 2:
                fb = classify_with_llm(_llm, msg, 'compare_models', candidates, all_names)
                if fb:
                    if fb.get('models') and len(fb['models']) >= 2:
                        candidates = fb['models']
                    if not level and fb.get('cefr_level'):
                        level = fb['cefr_level']
                    if not cat and fb.get('category'):
                        cat = fb['category']

        if len(candidates) < 2:
            session.reply(_t('compare_need_two', lang))
            return

        if not level:
            session.reply(_t('ask_cefr_level', lang, m1=candidates[0], m2=candidates[1]))
            return

        if not cat:
            cat = "Total"

        rows = compare_models(candidates[:3], level, cat)

        if not rows:
            session.reply(_t('score_not_found', lang, level=level, cat=cat, model=', '.join(candidates[:3])))
            return

        if len(rows) == 1:
            _reply(session,
                f"I only found a result for **{rows[0]['model_name']}** "
                f"({level} {cat}: **{rows[0]['score']:.2f}%**). "
                "I could not find a matching result for the other model."
            )
            return

        header = f"**{level} {cat} — comparison**\n\n"
        lines = [
            f"{i+1}. **{r['model_name']}** — {r['score']:.2f}%"
            for i, r in enumerate(rows)
        ]
        if len(rows) == 2:
            delta = abs(rows[0]['score'] - rows[1]['score'])
            leader = rows[0]['model_name']
            lines.append(
                f"\n*{leader} leads by **{delta:.2f} percentage points**.*"
            )

        _reply(session, header + "\n".join(lines))
    except Exception:
        baf_logger.error("compare_models_body failed:\n%s", traceback.format_exc())
        session.reply(_t('error', _lang(session)))


compare_models_state.set_body(compare_models_body)


# ── Filter results ────────────────────────────────────────────────────────────

def filter_results_body(session: Session) -> None:
    try:
        msg = _get_user_message(session)
        route = _consume_llm_route(session)

        level     = (route.get('cefr_level') if route else None) or extract_cefr_level(msg)
        cat       = (route.get('category')   if route else None) or extract_category(msg)
        # Use LLM-extracted licensing first; fall back to entity extraction from raw text
        licensing = (route.get('licensing') if route else None) or extract_licensing(msg)

        # Detect family mentions (basic heuristic)
        family = None
        msg_lower = msg.lower()
        for f in get_model_families():
            if f.lower() in msg_lower:
                family = f
                break

        filters: dict = {}
        if level:
            filters["cefrLevel"] = level
        if cat:
            filters["testCategory"] = cat
        if licensing:
            filters["licensingType"] = licensing
        if family:
            filters["family"] = family

        if not filters:
            session.reply(_t('filter_unrecognized', _lang(session)))
            return

        lang = _lang(session)
        parts = []
        if "cefrLevel" in filters:
            parts.append(f"CEFR level **{filters['cefrLevel']}**")
        if "testCategory" in filters:
            parts.append(f"category **{filters['testCategory']}**")
        if "licensingType" in filters:
            parts.append(f"**{filters['licensingType'].replace('_', ' ')}** models")
        if "family" in filters:
            parts.append(f"**{filters['family']}** family")

        session.reply(_t('filter_applied', lang, parts=', '.join(parts)))
        _send_ui_action(session, {"type": "apply_filters", "filters": filters})
    except Exception:
        baf_logger.error("filter_results_body failed:\n%s", traceback.format_exc())
        session.reply(_t('error', _lang(session)))


filter_results_state.set_body(filter_results_body)


# ── Reset view ────────────────────────────────────────────────────────────────

def reset_view_body(session: Session) -> None:
    try:
        msg = _get_user_message(session)
        lower = msg.lower()
        _consume_llm_route(session)

        fields = []
        if "cefr" in lower or "level" in lower:
            fields.append("cefrLevel")
        if "category" in lower or "grammar" in lower or "vocab" in lower or "listening" in lower or "reading" in lower:
            fields.append("testCategory")
        if "licens" in lower or "open" in lower or "proprietary" in lower or "closed" in lower:
            fields.append("licensingType")
        if "performance" in lower or "threshold" in lower or "percent" in lower or "minimum" in lower:
            fields.append("minPerformance")

        lang = _lang(session)
        if fields:
            field_labels = ", ".join(f"**{f}**" for f in fields)
            session.reply(_t('reset_fields', lang, fields=field_labels))
            _send_ui_action(session, {"type": "reset_filters", "fields": fields})
        else:
            session.reply(_t('reset_all', lang))
            _send_ui_action(session, {"type": "reset_filters"})
    except Exception:
        baf_logger.error("reset_view_body failed:\n%s", traceback.format_exc())
        session.reply(_t('error', _lang(session)))


reset_view_state.set_body(reset_view_body)


# ── Data coverage ─────────────────────────────────────────────────────────────

def data_coverage_body(session: Session) -> None:
    try:
        msg = _get_user_message(session)
        all_names = _get_all_names()
        _consume_llm_route(session)

        candidates = resolve_model_name(msg, all_names)
        if candidates and any(kw in msg.lower() for kw in ("include", "in the", "listed", "appear", "is model")):
            matches = [n for n in candidates if n.lower() in msg.lower() or any(
                w in n.lower() for w in msg.lower().split() if len(w) >= 4
            )]
            if matches:
                _reply(session,
                    f"Yes, **{matches[0]}** is included in the leaderboard with results "
                    f"across all 31 metrics (6 CEFR levels × 4 categories + Macro Average)."
                )
            else:
                _reply(session,
                    "I couldn't find that model. Try searching with the exact name as shown in the table."
                )
            return

        stats = get_coverage_stats()
        families = get_model_families()
        _reply(session,
            f"**LëtzEval leaderboard coverage:**\n\n"
            f"• **{stats['model_count']} models** evaluated\n"
            f"• **{stats['open_source']} open-source** and **{stats['proprietary']} proprietary** models\n"
            f"• **{stats['families']} model families** represented: {', '.join(families[:10])}"
            + (" ..." if len(families) > 10 else "") + "\n"
            f"• **6 CEFR levels**: A1, A2, B1, B2, C1, C2\n"
            f"• **4 task categories**: Grammar, Vocabulary, Reading Comprehension, Listening Comprehension\n"
            f"• **31 metrics** per model (5 per level + Macro Average)\n"
            f"• All models have complete results across all metrics"
        )
    except Exception:
        baf_logger.error("data_coverage_body failed:\n%s", traceback.format_exc())
        session.reply(_t('error', _lang(session)))


data_coverage_state.set_body(data_coverage_body)


# ── Out of scope ──────────────────────────────────────────────────────────────

def out_of_scope_body(session: Session) -> None:
    _consume_llm_route(session)
    session.reply(_t('out_of_scope', _lang(session)))


out_of_scope_state.set_body(out_of_scope_body)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from http_wrapper import start_http_bridge
    start_http_bridge()
    agent.run()
