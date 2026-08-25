"""Live web search + contest-aware anti-cheat helpers."""

from __future__ import annotations

import json
import re
from html import unescape
from typing import Any
from urllib.parse import quote_plus, urlencode
from urllib.request import Request, urlopen

UA = "agent-olympiad-research/1.0"


LEAK_MARKERS = (
    "official solution",
    "answer key",
    "marking scheme",
    "solutions pdf",
    "past paper answers",
    "cheat sheet answers",
    "site:aops.com solution",
)


def looks_like_answer_lookup(query: str) -> bool:
    lowered = (query or "").lower()
    return any(marker in lowered for marker in LEAK_MARKERS)


def duckduckgo_instant(query: str, *, max_results: int = 5, timeout: float = 15.0) -> dict[str, Any]:
    """Query DuckDuckGo Instant Answer API (no key). Returns structured snippets."""
    params = urlencode({"q": query, "format": "json", "no_html": 1, "skip_disambig": 1})
    url = f"https://api.duckduckgo.com/?{params}"
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8", errors="replace"))

    results: list[dict[str, str]] = []
    abstract = (payload.get("AbstractText") or "").strip()
    if abstract:
        results.append(
            {
                "title": payload.get("Heading") or "Abstract",
                "snippet": abstract,
                "url": payload.get("AbstractURL") or "",
            }
        )
    for topic in payload.get("RelatedTopics") or []:
        if len(results) >= max_results:
            break
        if isinstance(topic, dict) and topic.get("Text"):
            results.append(
                {
                    "title": (topic.get("Text") or "")[:80],
                    "snippet": topic.get("Text") or "",
                    "url": topic.get("FirstURL") or "",
                }
            )
        elif isinstance(topic, dict):
            for nested in topic.get("Topics") or []:
                if len(results) >= max_results:
                    break
                if nested.get("Text"):
                    results.append(
                        {
                            "title": (nested.get("Text") or "")[:80],
                            "snippet": nested.get("Text") or "",
                            "url": nested.get("FirstURL") or "",
                        }
                    )
    return {"query": query, "provider": "duckduckgo_instant", "results": results}


def duckduckgo_html_fallback(query: str, *, max_results: int = 5, timeout: float = 15.0) -> dict[str, Any]:
    """Lightweight HTML scrape fallback when instant answers are empty."""
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=timeout) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    results: list[dict[str, str]] = []
    for block in re.findall(
        r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?class="result__snippet"[^>]*>(.*?)</(?:a|td|div)',
        html,
        re.S | re.I,
    ):
        href, title, snippet = block
        results.append(
            {
                "title": re.sub(r"<[^>]+>", "", unescape(title)).strip(),
                "snippet": re.sub(r"<[^>]+>", "", unescape(snippet)).strip(),
                "url": unescape(href),
            }
        )
        if len(results) >= max_results:
            break
    return {"query": query, "provider": "duckduckgo_html", "results": results}


def live_web_search(query: str, *, max_results: int = 5) -> str:
    """Return a compact agent-readable search report."""
    query = (query or "").strip()
    if not query:
        return "web_search error: empty query."
    try:
        payload = duckduckgo_instant(query, max_results=max_results)
        if not payload["results"]:
            payload = duckduckgo_html_fallback(query, max_results=max_results)
    except Exception as exc:
        return f"web_search error: {exc}"

    if not payload["results"]:
        return f"[web_search | {payload['provider']}] No results for: {query}"

    lines = [f"[web_search | {payload['provider']}] Query: {query}"]
    for i, item in enumerate(payload["results"], 1):
        lines.append(f"{i}. {item.get('title') or '(untitled)'}")
        if item.get("snippet"):
            lines.append(f"   {item['snippet'][:400]}")
        if item.get("url"):
            lines.append(f"   URL: {item['url']}")
    lines.append(
        "Policy reminder: use sources for background facts only — "
        "do not look up contest answer keys or official solutions."
    )
    return "\n".join(lines)
