from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass
class RankerConfig:
    category_weights: dict[str, float] = field(default_factory=dict)
    recency_weight: float = 0.4
    keyword_hit_weight: float = 1.2
    code_link_bonus: float = 0.5
    min_score: float = 1.2


@dataclass
class SummaryConfig:
    hotspot_top_n: int = 8
    event_top_n: int = 5


@dataclass
class ScheduleConfig:
    time: str = "08:00"
    timezone: str = "Asia/Shanghai"


@dataclass
class LLMConfig:
    api_key: str | None = None
    base_url: str | None = None
    model: str = "gpt-4.1-mini"

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)


@dataclass
class AppConfig:
    keywords: list[str]
    categories: list[str]
    days_back: int
    max_results: int
    top_k: int
    output_dir: Path
    site_dir: Path
    schedule: ScheduleConfig
    ranker: RankerConfig
    summary: SummaryConfig
    llm: LLMConfig


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(config_path: str | Path | None = None) -> AppConfig:
    load_dotenv()

    root = Path(__file__).resolve().parent.parent
    path = Path(config_path) if config_path else root / "config.yaml"
    raw = _load_yaml(path)

    ranker_raw = raw.get("ranker", {})
    summary_raw = raw.get("summary", {})
    schedule_raw = raw.get("schedule", {})

    return AppConfig(
        keywords=list(raw.get("keywords", [])),
        categories=list(raw.get("categories", [])),
        days_back=int(raw.get("days_back", 2)),
        max_results=int(raw.get("max_results", 60)),
        top_k=int(raw.get("top_k", 15)),
        output_dir=root / raw.get("output_dir", "output"),
        site_dir=root / raw.get("site_dir", "site"),
        schedule=ScheduleConfig(
            time=str(schedule_raw.get("time", "08:00")),
            timezone=str(schedule_raw.get("timezone", "Asia/Shanghai")),
        ),
        ranker=RankerConfig(
            category_weights=dict(ranker_raw.get("category_weights", {})),
            recency_weight=float(ranker_raw.get("recency_weight", 0.4)),
            keyword_hit_weight=float(ranker_raw.get("keyword_hit_weight", 1.2)),
            code_link_bonus=float(ranker_raw.get("code_link_bonus", 0.5)),
            min_score=float(ranker_raw.get("min_score", 1.2)),
        ),
        summary=SummaryConfig(
            hotspot_top_n=int(summary_raw.get("hotspot_top_n", 8)),
            event_top_n=int(summary_raw.get("event_top_n", 5)),
        ),
        llm=LLMConfig(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        ),
    )
