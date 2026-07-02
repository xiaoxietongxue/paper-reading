from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import feedparser
import requests

from paper_reading.config import AppConfig
from paper_reading.models import Paper

logger = logging.getLogger(__name__)

ARXIV_API_URL = "http://export.arxiv.org/api/query"
ARXIV_ID_PATTERN = re.compile(r"arxiv\.org/abs/([^/?#]+)")


def _extract_arxiv_id(entry_id: str) -> str:
    match = ARXIV_ID_PATTERN.search(entry_id)
    if match:
        return match.group(1)
    # fallback: last path segment
    return entry_id.rstrip("/").split("/")[-1]


def _parse_datetime(value: str) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        dt = datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S")
        dt = dt.replace(tzinfo=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _build_query(keyword: str, categories: list[str]) -> str:
    keyword_part = f'all:"{keyword}"'
    if not categories:
        return keyword_part
    category_part = " OR ".join(f"cat:{cat}" for cat in categories)
    return f"({keyword_part}) AND ({category_part})"


def _parse_entry(entry: dict, matched_keyword: str) -> Paper | None:
    arxiv_id = _extract_arxiv_id(entry.get("id", ""))
    if not arxiv_id:
        return None

    title = " ".join(entry.get("title", "").split())
    abstract = " ".join(entry.get("summary", "").split())
    authors = [author.get("name", "") for author in entry.get("authors", [])]
    categories = [tag.get("term", "") for tag in entry.get("tags", []) if tag.get("term")]
    published = _parse_datetime(entry.get("published", ""))
    updated = _parse_datetime(entry.get("updated", published.isoformat()))

    return Paper(
        arxiv_id=arxiv_id,
        title=title,
        authors=authors,
        abstract=abstract,
        categories=categories,
        url=f"https://arxiv.org/abs/{arxiv_id}",
        published=published,
        updated=updated,
        matched_keywords=[matched_keyword],
    )


def _fetch_keyword(keyword: str, config: AppConfig) -> list[Paper]:
    query = _build_query(keyword, config.categories)
    params = {
        "search_query": query,
        "start": 0,
        "max_results": config.max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API_URL}?{urlencode(params)}"
    logger.info("Fetching arxiv papers for keyword: %s", keyword)

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    feed = feedparser.parse(response.text)

    cutoff = datetime.now(timezone.utc) - timedelta(days=config.days_back)
    papers: list[Paper] = []
    for entry in feed.entries:
        paper = _parse_entry(entry, keyword)
        if paper is None:
            continue
        if paper.published < cutoff:
            continue
        papers.append(paper)
    return papers


def fetch_papers(config: AppConfig) -> list[Paper]:
    seen: dict[str, Paper] = {}

    for keyword in config.keywords:
        try:
            papers = _fetch_keyword(keyword, config)
        except requests.RequestException as exc:
            logger.error("Failed to fetch keyword '%s': %s", keyword, exc)
            continue

        for paper in papers:
            existing = seen.get(paper.arxiv_id)
            if existing is None:
                seen[paper.arxiv_id] = paper
            else:
                for kw in paper.matched_keywords:
                    if kw not in existing.matched_keywords:
                        existing.matched_keywords.append(kw)

        # arxiv API rate limit: 1 request every 3 seconds
        time.sleep(3)

    result = list(seen.values())
    result.sort(key=lambda p: p.published, reverse=True)
    logger.info("Fetched %d unique papers", len(result))
    return result
