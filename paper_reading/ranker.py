from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from paper_reading.config import AppConfig
from paper_reading.models import Paper

logger = logging.getLogger(__name__)

CODE_LINK_PATTERN = re.compile(
    r"(github\.com|gitlab\.com|huggingface\.co|project page|code available|open-source|open source)",
    re.IGNORECASE,
)


def _recency_score(paper: Paper, now: datetime) -> float:
    age_days = max((now - paper.published).total_seconds() / 86400, 0.0)
    if age_days <= 1:
        return 1.0
    if age_days <= 3:
        return 0.7
    if age_days <= 7:
        return 0.4
    return 0.1


def _category_score(paper: Paper, weights: dict[str, float]) -> float:
    if not paper.categories:
        return 1.0
    matched = [weights.get(cat, 1.0) for cat in paper.categories]
    return max(matched)


def score_paper(paper: Paper, config: AppConfig, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    ranker = config.ranker

    keyword_score = len(paper.matched_keywords) * ranker.keyword_hit_weight
    recency = _recency_score(paper, now) * ranker.recency_weight
    category = _category_score(paper, ranker.category_weights)
    code_bonus = ranker.code_link_bonus if CODE_LINK_PATTERN.search(paper.abstract) else 0.0

    paper.score = keyword_score + recency + category + code_bonus
    return paper.score


def rank_papers(papers: list[Paper], config: AppConfig) -> list[Paper]:
    now = datetime.now(timezone.utc)
    for paper in papers:
        score_paper(paper, config, now)

    filtered = [p for p in papers if p.score >= config.ranker.min_score]
    filtered.sort(key=lambda p: p.score, reverse=True)
    top = filtered[: config.top_k]
    logger.info("Ranked %d papers, selected top %d", len(papers), len(top))
    return top
