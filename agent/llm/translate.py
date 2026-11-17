"""
LLM-powered response translation for the LëtzEval BAF assistant.

Called when the session language is not English to translate the
agent's English-only data responses (rankings, scores, explanations)
into the user's chosen language.

Static messages already handled by intents/i18n.py are not passed here.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_LANG_NAMES: dict[str, str] = {
    'de': 'German',
    'fr': 'French',
    'it': 'Italian',
    'lb': 'Luxembourgish',
    'pt': 'Portuguese',
}

_SYSTEM_TMPL = (
    "Translate the following LLM leaderboard assistant response to {lang_name}.\n"
    "Rules:\n"
    "- Keep model names exactly as written (e.g. 'GPT-6 Astra', 'Qwen 3 - 14B').\n"
    "- Keep CEFR level codes unchanged: A1 A2 B1 B2 C1 C2.\n"
    "- Keep category names unchanged: Grammar, Vocabulary, Reading Comprehension, "
    "Listening Comprehension, Macro Average, Total.\n"
    "- Keep percentages and numeric values unchanged.\n"
    "- Keep markdown formatting (**bold**, *italic*, bullet points) exactly.\n"
    "- Keep 'LëtzEval' unchanged.\n"
    "Return ONLY the translated text — no explanation, no markdown fences."
)


def translate_text(llm, text: str, lang: str) -> Optional[str]:
    """Translate *text* to *lang* using *llm*.

    Returns the translated string, or None when translation is unavailable
    or fails (caller should fall back to the original English text).
    """
    lang_name = _LANG_NAMES.get(lang)
    if not lang_name or not text or not text.strip() or llm is None:
        return None

    system = _SYSTEM_TMPL.format(lang_name=lang_name)
    is_openai = type(llm).__name__ == 'LLMOpenAI'

    if is_openai:
        model_id = (getattr(llm, 'parameters', None) or {}).get('model', 'gpt-4o-mini')
        try:
            resp = llm.client.chat.completions.create(
                model=model_id,
                messages=[
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': text},
                ],
                max_completion_tokens=1200,
                temperature=0.1,
            )
            result = resp.choices[0].message.content
            return result.strip() if result else None
        except Exception as exc:
            logger.warning("Translation failed (OpenAI): %s", exc)
            return None
    else:
        try:
            result = llm.predict(
                message=text,
                parameters={'max_tokens': 1200, 'temperature': 0.1},
                system_message=system,
            )
            return result.strip() if result else None
        except Exception as exc:
            logger.warning("Translation failed (%s): %s", type(llm).__name__, exc)
            return None
