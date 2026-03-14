"""
main.py – CLI entry point for the AI Research Agent.

Usage:
    python main.py                            # uses default query
    python main.py "Your custom query here"   # pass query as argument
"""

import sys
import os
import time
import argparse
from datetime import datetime

from agents.search_agent import run_search_agent
from chains.summarizer import summarize
from agents.report_agent import generate_report
from utils.pdf_exporter import export_pdf


# ── Helpers ───────────────────────────────────────────────────────────────────

def _print_divider(char: str = "─", width: int = 60) -> None:
    print(char * width)


def _print_step(step: int, total: int, message: str) -> None:
    print(f"\n  [{step}/{total}] {message}")


# ── Core pipeline ─────────────────────────────────────────────────────────────

def main(query: str, output_dir: str = ".") -> str:
    """
    Run the full research pipeline for *query*.

    Args:
        query:      The research question.
        output_dir: Directory where the PDF report will be saved.

    Returns:
        The generated Markdown report as a string.
    """
    if not query or not query.strip():
        raise ValueError("Query must be a non-empty string.")

    os.makedirs(output_dir, exist_ok=True)

    _print_divider("═")
    print("  🧠  AI Research Agent")
    print(f"  Query : {query}")
    print(f"  Time  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    _print_divider("═")

    start = time.time()

    # ── Step 1: Search ────────────────────────────────────────────────────────
    _print_step(1, 3, "Searching the web…")
    results = run_search_agent(query)

    if not results or "results" not in results or not results["results"]:
        raise RuntimeError(
            "Search returned no results. "
            "Check your Tavily API key and network connection."
        )

    content: str = ""
    sources: list[str] = []

    for r in results["results"]:
        content += r.get("content", "") + "\n\n"
        url = r.get("url", "").strip()
        if url:
            sources.append(url)

    print(f"     ✓  {len(sources)} source(s) collected.")

    # ── Step 2: Summarise ─────────────────────────────────────────────────────
    _print_step(2, 3, "Analysing content with Gemini AI…")
    summary = summarize(content)

    if summary.startswith("Error"):
        raise RuntimeError(f"Summarisation failed: {summary}")

    print("     ✓  Summary generated.")

    # ── Step 3: Build & export report ─────────────────────────────────────────
    _print_step(3, 3, "Composing final report…")
    report = generate_report(summary, sources)

    # Build a safe filename from the query
    safe_query = "".join(c if c.isalnum() or c in " _-" else "_" for c in query)
    safe_query = safe_query[:50].strip().replace(" ", "_")
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_name   = f"research_{safe_query}_{timestamp}.pdf"
    pdf_path   = os.path.join(output_dir, pdf_name)

    success = export_pdf(report, pdf_path)

    elapsed = time.time() - start
    _print_divider()
    if success:
        print(f"  ✅  Report saved → {pdf_path}  ({elapsed:.1f}s)")
    else:
        print(f"  ⚠️   PDF export failed; report printed below.  ({elapsed:.1f}s)")
    _print_divider()

    print("\n" + report)
    return report


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AI Research Agent – generate a researched PDF report from a query."
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="Impact of AI agents on software development",
        help="Research question (default: Impact of AI agents on software development)",
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Directory to save the PDF report (default: ./reports)",
    )
    args = parser.parse_args()

    try:
        main(args.query, output_dir=args.output_dir)
    except (ValueError, RuntimeError) as exc:
        print(f"\n  ❌  {exc}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n  Interrupted.")
        sys.exit(0)