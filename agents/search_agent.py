from tools.search_tool import search_web

def run_search_agent(query):
    return search_web(query)
"""
agents/search_agent.py – Web-search agent powered by Tavily.

Exports
-------
run_search_agent(query)  → dict   (the function expected by main.py / app.py)
search_web(query)        → dict   (thin alias kept for backwards-compatibility)
"""

import logging
from typing import Any

from tavily import TavilyClient, MissingAPIKeyError
from config import TAVILY_API_KEY

logger = logging.getLogger(__name__)

# ── Client ────────────────────────────────────────────────────────────────────

def _make_client() -> TavilyClient | None:
    """Return a TavilyClient if the API key looks valid, else None."""
    if not TAVILY_API_KEY or not TAVILY_API_KEY.startswith("tvly"):
        logger.error(
            "TAVILY_API_KEY is missing or invalid. "
            "Set it in your .env file (must start with 'tvly')."
        )
        return None
    return TavilyClient(api_key=TAVILY_API_KEY)


_client: TavilyClient | None = _make_client()


# ── Internal helpers ──────────────────────────────────────────────────────────

def _normalise_results(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Ensure every result entry has at least 'content' and 'url' keys.
    Tavily returns 'content' and 'url'; older SDKs may use slightly
    different field names – we handle both gracefully.
    """
    normalised = []
    for item in raw.get("results", []):
        normalised.append(
            {
                "url":     item.get("url", item.get("link", "")),
                "content": item.get("content", item.get("body", item.get("snippet", ""))),
                "title":   item.get("title", ""),
                "score":   item.get("score", 0.0),
            }
        )
    return {**raw, "results": normalised}


# ── Public API ────────────────────────────────────────────────────────────────

def run_search_agent(
    query: str,
    max_results: int = 5,
    search_depth: str = "advanced",
    include_answer: bool = True,
) -> dict[str, Any]:
    """
    Search the web for *query* and return a normalised result dict.

    Args:
        query:          The research question.
        max_results:    Maximum number of results to retrieve (default 5).
        search_depth:   'basic' or 'advanced' (default 'advanced').
        include_answer: Whether Tavily should include a direct answer summary.

    Returns:
        A dict with at least a 'results' key containing a list of
        {'url', 'content', 'title', 'score'} dicts.

    Raises:
        RuntimeError: If the client is not configured or the API call fails.
    """
    if not query or not query.strip():
        raise ValueError("Search query must be a non-empty string.")

    if _client is None:
        raise RuntimeError(
            "Tavily client is not initialised. "
            "Ensure TAVILY_API_KEY is set correctly in your .env file."
        )

    logger.info("Searching Tavily for: %r (depth=%s, max=%d)", query, search_depth, max_results)

    try:
        raw = _client.search(
            query,
            max_results=max_results,
            search_depth=search_depth,
            include_answer=include_answer,
        )
    except MissingAPIKeyError:
        raise RuntimeError("Tavily rejected the API key. Check TAVILY_API_KEY in .env.")
    except Exception as exc:
        logger.exception("Tavily search failed.")
        raise RuntimeError(f"Search request failed: {exc}") from exc

    results = _normalise_results(raw)

    if not results.get("results"):
        logger.warning("Tavily returned zero results for query: %r", query)

    logger.info("Tavily returned %d result(s).", len(results["results"]))
    return results


# Backwards-compatible alias
def search_web(
    query: str,
    max_results: int = 5,
) -> dict[str, Any]:
    """Thin alias for run_search_agent (kept for backwards compatibility)."""
    return run_search_agent(query, max_results=max_results)