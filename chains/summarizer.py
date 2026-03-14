"""
chains/summarizer.py – Content summarisation chain using Google Gemini.

Model  : gemini-1.5-flash  (free tier, 1 M token context window)
Library: langchain-google-genai
"""

import logging
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from config import GOOGLE_API_KEY, GROQ_API_KEY
logger = logging.getLogger(__name__)


# ── Guard: fail fast with a clear message ─────────────────────────────────────

if not GOOGLE_API_KEY or not GOOGLE_API_KEY.startswith("AIza"):
    raise EnvironmentError(
        "GOOGLE_API_KEY is missing or invalid. "
        "Set it in your .env file (must start with 'AIza')."
    )


# ── Model ─────────────────────────────────────────────────────────────────────

_llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API_KEY)

# _llm = ChatGoogleGenerativeAI(
    # model="gemini-2.0-flash",       # Free tier; change to "gemini-1.5-pro" for richer output
    # google_api_key=GOOGLE_API_KEY,
    # temperature=0.4,                # Lower = more factual / less hallucination
    # max_tokens=2048,
    # Retry config: Gemini free tier may rate-limit at 60 req/min
    # max_retries=3,
# )


# ── Prompt ────────────────────────────────────────────────────────────────────

_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["text"],
    template="""You are a professional research analyst. Your task is to produce a \
clear, structured summary of the raw web-search content below.

Guidelines:
- Identify and highlight the **main findings** and key insights.
- Preserve specific facts, figures, dates, and names where relevant.
- Group related points into thematic clusters.
- Keep the summary concise but comprehensive (aim for 300–500 words).
- Write in plain, formal English – avoid jargon or filler phrases.
- Do NOT invent information that is not present in the source text.

---
SOURCE CONTENT:
{text}
---

SUMMARY:""",
)

_chain = _SUMMARY_PROMPT | _llm | StrOutputParser()


# ── Chunking helper ───────────────────────────────────────────────────────────

_MAX_CHARS = 60_000   # ~15 k tokens – safely within Gemini Flash's free-tier limits


def _chunk_text(text: str, max_chars: int = _MAX_CHARS) -> list[str]:
    """
    Split *text* into chunks of at most *max_chars* characters,
    splitting on paragraph boundaries where possible.
    """
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in text.split("\n\n"):
        para_len = len(para) + 2  # +2 for the "\n\n"
        if current_len + para_len > max_chars and current:
            chunks.append("\n\n".join(current))
            current = []
            current_len = 0
        current.append(para)
        current_len += para_len

    if current:
        chunks.append("\n\n".join(current))

    return chunks


# ── Public function ───────────────────────────────────────────────────────────

def summarize(
    text: str,
    max_chars: int = _MAX_CHARS,
    title: Optional[str] = None,
) -> str:
    """
    Summarise *text* using Gemini 1.5 Flash.

    If *text* exceeds *max_chars* it is split into chunks; each chunk is
    summarised individually and the partial summaries are merged with a
    second Gemini call.

    Args:
        text:      Raw content to summarise (plain text or light Markdown).
        max_chars: Maximum characters per Gemini call (default 60 000).
        title:     Optional topic label printed in log messages.

    Returns:
        A structured Markdown summary string.

    Raises:
        RuntimeError: If all Gemini calls fail.
    """
    if not text or not text.strip():
        logger.warning("summarize() called with empty text; returning empty string.")
        return ""

    label = f'"{title}"' if title else "content"
    logger.info("Summarising %s (%d chars)…", label, len(text))

    chunks = _chunk_text(text, max_chars=max_chars)

    if len(chunks) == 1:
        return _invoke(chunks[0])

    # Multi-chunk path: summarise each chunk then merge
    logger.info("Text split into %d chunk(s); summarising each individually.", len(chunks))
    partial: list[str] = []

    for i, chunk in enumerate(chunks, 1):
        logger.debug("Summarising chunk %d/%d…", i, len(chunks))
        partial.append(_invoke(chunk))

    if len(partial) == 1:
        return partial[0]

    # Merge partial summaries
    logger.info("Merging %d partial summaries…", len(partial))
    merged_text = "\n\n---\n\n".join(partial)
    merge_note  = (
        "The following are partial summaries of different sections of a larger document. "
        "Merge them into a single coherent summary, removing duplication.\n\n"
        + merged_text
    )
    return _invoke(merge_note)


def _invoke(text: str) -> str:
    """Call the LangChain chain with error handling."""
    try:
        result = _chain.invoke({"text": text})
        return result.strip() if result else ""
    except Exception as exc:
        logger.exception("Gemini invocation failed.")
        raise RuntimeError(f"Summarisation failed: {exc}") from exc