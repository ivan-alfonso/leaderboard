"""
Input sanitization for the LëtzEval BAF agent.

Normalizes Unicode and whitespace, strips control characters, validates
maximum message length, and preserves meaningful model-version tokens
(digits, version numbers like 2.5, size tokens like 0.5B, 70B, 1.5B).

Punctuation that could distinguish model names (dots in "2.5", dashes in
"GPT-4o", slashes in version strings) is NEVER stripped blindly.
"""
import re
import unicodedata

MAX_INPUT_LENGTH = 500


def sanitize(text: str) -> str:
    """Normalize and validate a user input string.

    Returns a cleaned string safe to pass to the LLM interpreter.
    Preserves the original meaning and model-identifying tokens.
    """
    if not isinstance(text, str):
        return ''

    # NFC normalization — compose combining characters so "GPT‑" works like "GPT-"
    text = unicodedata.normalize('NFC', text)

    # Strip control characters except \n \r \t
    # Category 'Cc' = C0/C1 controls; 'Cf' = format characters (zero-width, BOM, etc.)
    text = ''.join(
        c for c in text
        if unicodedata.category(c) not in ('Cc', 'Cf') or c in ('\n', '\r', '\t')
    )

    # Normalize all whitespace variations to a single space
    # Includes non-breaking spaces, thin spaces, ideographic spaces, etc.
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'[\xa0 -‏  　­]+', ' ', text)
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()

    # Truncate at word boundary to preserve model-version tokens
    if len(text) > MAX_INPUT_LENGTH:
        truncated = text[:MAX_INPUT_LENGTH]
        last_space = truncated.rfind(' ')
        text = truncated[:last_space] if last_space > 0 else truncated

    return text
