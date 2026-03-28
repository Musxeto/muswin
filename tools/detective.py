"""OSINT-style public footprint lookup for Muswin."""

from __future__ import annotations

from duckduckgo_search import DDGS


def _dork_queries(identity: str) -> list[str]:
    token = identity.strip()
    return [
        f'"{token}" site:github.com',
        f'"{token}" site:reddit.com',
        f'"{token}" site:news.ycombinator.com',
        f'"{token}" site:medium.com',
        f'"{token}" "profile"',
    ]


def osint_lookup(identity: str, max_results_per_query: int = 4) -> str:
    """Search public mentions using search operators and aggregate output."""

    identity = identity.strip()
    if not identity:
        return "No identity provided."

    lines: list[str] = [f"OSINT lookup for: {identity}"]
    seen_links: set[str] = set()

    with DDGS() as ddgs:
        for query in _dork_queries(identity):
            lines.append(f"\nQuery: {query}")
            count = 0
            for result in ddgs.text(query, max_results=max_results_per_query):
                title = str(result.get("title", "")).strip()
                href = str(result.get("href", "")).strip()
                snippet = str(result.get("body", "")).strip()

                if not href or href in seen_links:
                    continue

                seen_links.add(href)
                count += 1
                lines.append(f"- {title} | {href}")
                if snippet:
                    lines.append(f"  {snippet}")

            if count == 0:
                lines.append("- No unique results")

    if len(seen_links) == 0:
        lines.append("\nNo public traces found in this pass.")

    return "\n".join(lines)
