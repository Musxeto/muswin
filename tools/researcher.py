"""Web research helper for Muswin."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS


def _top_links(query: str, max_results: int = 3) -> list[str]:
    links: list[str] = []
    with DDGS() as ddgs:
        for result in ddgs.text(query, max_results=max_results):
            href = str(result.get("href", "")).strip()
            if href:
                links.append(href)
    return links


def _extract_paragraph_text(url: str, timeout: float = 12.0) -> str:
    try:
        response = requests.get(url, timeout=timeout, headers={"User-Agent": "MuswinResearchBot/1.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        cleaned = "\n".join(line for line in paragraphs if line)
        return cleaned[:9000]
    except Exception as exc:  # noqa: BLE001
        return f"Failed to read {url}: {exc}"


def search_web(query: str) -> str:
    """Return compiled source text from top search results."""

    links = _top_links(query, max_results=3)
    if not links:
        return "No search results found."

    chunks: list[str] = []
    for index, link in enumerate(links, start=1):
        body = _extract_paragraph_text(link)
        chunks.append(f"Source {index}: {link}\n{body}\n")

    return "\n".join(chunks)


def save_markdown_report(query: str, content: str, file_name: str | None = None) -> str:
    """Save a markdown report to the Desktop."""

    desktop = Path.home() / "Desktop"
    desktop.mkdir(parents=True, exist_ok=True)

    if not file_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"muswin_research_{timestamp}.md"

    report_path = desktop / file_name
    report = (
        f"# Muswin Research Report\n\n"
        f"Query: {query}\n\n"
        f"Generated: {datetime.now().isoformat()}\n\n"
        f"## Findings\n\n{content}\n"
    )
    report_path.write_text(report, encoding="utf-8")
    return str(report_path)
