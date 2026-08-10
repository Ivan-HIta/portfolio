"""Safe, local-first ticket summarization utilities.

The default summary path is deterministic and extractive so the app works
without credentials, network access, or sensitive data leaving the machine.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable
from typing import Any

try:
    from .preprocessing import clean_text
except ImportError:  # pragma: no cover - direct module convenience
    from preprocessing import clean_text


_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "because", "by", "for", "from", "has", "in", "is", "it", "of", "on",
    "or", "that", "the", "this", "to", "was", "with", "after", "before", "between", "due", "requires", "require",
}


def _sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", str(text).strip()) if sentence.strip()]


def extractive_summary(description: str, max_sentences: int = 1, max_words: int = 32) -> str:
    """Create a concise, reproducible summary using salient source sentences."""
    if max_sentences < 1 or max_words < 1:
        raise ValueError("max_sentences and max_words must be positive")
    sentences = _sentences(description)
    if not sentences:
        return "No ticket description was provided."
    if len(sentences) == 1 and len(sentences[0].split()) <= max_words:
        return sentences[0]

    tokens = [token for token in clean_text(description).split() if token not in _STOP_WORDS and len(token) > 2]
    frequencies = Counter(tokens)
    ranked: list[tuple[int, float, str]] = []
    for index, sentence in enumerate(sentences):
        sentence_tokens = [token for token in clean_text(sentence).split() if token not in _STOP_WORDS]
        score = sum(frequencies[token] for token in sentence_tokens) / max(1, len(sentence_tokens))
        ranked.append((index, score, sentence))
    selected = sorted(sorted(ranked, key=lambda item: (-item[1], item[0]))[:max_sentences], key=lambda item: item[0])

    words: list[str] = []
    for _, _, sentence in selected:
        for word in sentence.split():
            if len(words) >= max_words:
                break
            words.append(word)
        if len(words) >= max_words:
            break
    summary = " ".join(words)
    original_words = len(" ".join(sentences).split())
    if len(words) < original_words and summary and not summary.endswith((".", "!", "?")):
        summary += "…"
    return summary or "No ticket description was provided."


def summarize_ticket(
    description: str,
    max_sentences: int = 1,
    max_words: int = 32,
    llm_client: Callable[[str], str] | None = None,
) -> str:
    """Summarize a ticket, optionally using an injected approved LLM client.

    The application passes no client by default, providing a deterministic
    fallback. Injecting a callable keeps any future API integration outside of
    this portfolio project's core data path.
    """
    if llm_client is not None:
        try:
            candidate = str(llm_client(description)).strip()
            if candidate:
                return candidate
        except Exception:
            # A local app should keep triage available when an optional service fails.
            pass
    return extractive_summary(description, max_sentences=max_sentences, max_words=max_words)


def summarize_with_metadata(description: str, **kwargs: Any) -> dict[str, str]:
    """Return a UI-friendly summary plus the method used to produce it."""
    method = "optional_llm" if kwargs.get("llm_client") is not None else "deterministic_extractive"
    return {"summary": summarize_ticket(description, **kwargs), "method": method}
