def generate_report(summary, sources):
    sources_text = "\n".join(sources)
    report = f"""
# AI Research Report

## Summary
{summary}

## Sources
{sources_text}

## Final Insight
AI agents are transforming automation and research workflows.
"""
    return report