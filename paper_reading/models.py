from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Paper:
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    categories: list[str]
    url: str
    published: datetime
    updated: datetime
    matched_keywords: list[str] = field(default_factory=list)
    score: float = 0.0
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["published"] = self.published.isoformat()
        data["updated"] = self.updated.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Paper:
        return cls(
            arxiv_id=data["arxiv_id"],
            title=data["title"],
            authors=list(data.get("authors", [])),
            abstract=data.get("abstract", ""),
            categories=list(data.get("categories", [])),
            url=data.get("url", ""),
            published=datetime.fromisoformat(data["published"]),
            updated=datetime.fromisoformat(data["updated"]),
            matched_keywords=list(data.get("matched_keywords", [])),
            score=float(data.get("score", 0.0)),
            summary=data.get("summary", ""),
        )


@dataclass
class DailySummary:
    date: str
    hotspots: list[str]
    events: list[str]
    paper_summaries: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
