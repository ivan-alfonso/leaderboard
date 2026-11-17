"""
LLM provider configuration for the LëtzEval BAF assistant.

Reads environment variables at import time.  The factory function
`get_llm_provider()` returns a live LLM instance (LLMOpenAI or LLMOllama)
or None when provider is "none" or misconfigured.

Environment variables (set in .env or Docker env, never committed):
    LETZEVAL_LLM_PROVIDER       none | openai | ollama  (default: none)
    LETZEVAL_LLM_MODEL          model name for chosen provider
    OPENAI_API_KEY              required when provider=openai
    LETZEVAL_OLLAMA_BASE_URL    Ollama server (default: http://localhost:11434)
                                NOTE: 'localhost' refers to the container's own
                                loopback.  For a separate Ollama container use
                                the service name (e.g. http://ollama:11434).
    LETZEVAL_LLM_TIMEOUT_SECONDS  request timeout (default: 12)

Network note (Docker / AWS):
    'localhost' in Docker means the container itself, not the host machine.
    Use the Docker network service name or host.docker.internal (Mac/Win).
    On AWS, Ollama must be reachable on the same VPC / task network.
"""
import logging
import os

logger = logging.getLogger(__name__)

PROVIDER      = os.environ.get('LETZEVAL_LLM_PROVIDER', 'none').lower().strip()
MODEL         = os.environ.get('LETZEVAL_LLM_MODEL', '').strip()
OPENAI_KEY    = os.environ.get('OPENAI_API_KEY', '').strip()
OLLAMA_URL    = os.environ.get('LETZEVAL_OLLAMA_BASE_URL', 'http://localhost:11434').strip()
TIMEOUT       = int(os.environ.get('LETZEVAL_LLM_TIMEOUT_SECONDS', '12'))

# Allowed providers
VALID_PROVIDERS = {'none', 'openai', 'ollama'}


def get_llm_provider(agent=None):
    """Return a configured LLM instance, or None if provider is 'none'.

    The `agent` argument is required when creating a BAF LLM wrapper
    (BAF registers the LLM on the agent's NLP engine).  When agent is None,
    the wrapper is created in standalone/test mode; BAF integration features
    (e.g. intent classification) are unavailable.

    Returns:
        LLMOpenAI | LLMOllama | None
    """
    if PROVIDER == 'none' or not PROVIDER:
        return None

    if PROVIDER not in VALID_PROVIDERS:
        logger.warning("Unknown LETZEVAL_LLM_PROVIDER=%r; defaulting to none.", PROVIDER)
        return None

    try:
        if PROVIDER == 'openai':
            return _make_openai(agent)
        if PROVIDER == 'ollama':
            return _make_ollama(agent)
    except Exception as exc:
        logger.error("Failed to initialize LLM provider %r: %s", PROVIDER, exc)
        return None

    return None


def _make_openai(agent):
    """Create a BAF LLMOpenAI instance."""
    if not OPENAI_KEY:
        logger.error("LETZEVAL_LLM_PROVIDER=openai but OPENAI_API_KEY is not set.")
        return None

    model = MODEL or 'gpt-4o-mini'

    from baf.nlp.llm.llm_openai_api import LLMOpenAI

    llm = LLMOpenAI(
        agent=agent,
        name=model,
        parameters={'model': model, 'timeout': TIMEOUT},
        num_previous_messages=1,
    )
    # OPENAI_API_KEY is provided via environment (env_file / Docker env).
    # BAF's LLMOpenAI.initialize() passes it to OpenAI(api_key=...) automatically.
    # initialize() is called by BAF during agent.train() — do not call it here.
    logger.info("LLM provider: OpenAI model=%s timeout=%ss", model, TIMEOUT)
    return llm


def _make_ollama(agent):
    """Create a BAF LLMOllama instance."""
    model = MODEL or 'llama3.1'

    from baf.nlp.llm.llm_ollama import LLMOllama

    llm = LLMOllama(
        agent=agent,
        name=model,
        parameters={
            'base_url': OLLAMA_URL,
            'model': model,
            'timeout': TIMEOUT,
        },
        num_previous_messages=1,
    )
    # initialize() is called by BAF during agent.train() — do not call it here.
    logger.info("LLM provider: Ollama model=%s base_url=%s timeout=%ss", model, OLLAMA_URL, TIMEOUT)
    return llm
