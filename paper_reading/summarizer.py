from __future__ import annotations

import json
import logging
import re
from collections import Counter
from datetime import date

from openai import OpenAI

from paper_reading.config import AppConfig
from paper_reading.models import DailySummary, Paper

logger = logging.getLogger(__name__)

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "for", "on", "with", "by",
    "we", "our", "this", "that", "these", "those", "is", "are", "was", "were",
    "be", "been", "being", "from", "as", "at", "it", "its", "their", "they",
    "can", "may", "also", "using", "use", "used", "show", "shows", "based",
    "paper", "propose", "proposed", "approach", "method", "methods", "model",
    "models", "results", "demonstrate", "demonstrates", "via", "through",
}


def _first_sentence(text: str, max_len: int = 180) -> str:
    text = " ".join(text.split())
    if not text:
        return "暂无摘要。"
    parts = re.split(r"(?<=[.!?])\s+", text)
    sentence = parts[0] if parts else text
    if len(sentence) > max_len:
        return sentence[: max_len - 3] + "..."
    return sentence


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", text.lower())
    return [t for t in tokens if t not in STOPWORDS]


def _rule_paper_summary(paper: Paper) -> str:
    return _first_sentence(paper.abstract)


def _rule_hotspots(papers: list[Paper], top_n: int) -> list[str]:
    counter: Counter[str] = Counter()
    for paper in papers:
        counter.update(_tokenize(paper.title))
        counter.update(_tokenize(paper.abstract))
    return [f"{word} ({count})" for word, count in counter.most_common(top_n)]


def _rule_events(papers: list[Paper], top_n: int) -> list[str]:
    events: list[str] = []
    for paper in papers[:top_n]:
        events.append(f"{paper.title}（评分 {paper.score:.2f}）")
    return events


def _build_llm_client(config: AppConfig) -> OpenAI:
    kwargs: dict[str, str] = {"api_key": config.llm.api_key or ""}
    if config.llm.base_url:
        kwargs["base_url"] = config.llm.base_url
    return OpenAI(**kwargs)


def _llm_chat(client: OpenAI, model: str, system_prompt: str, user_prompt: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    content = response.choices[0].message.content
    return content.strip() if content else ""


def _llm_paper_summaries(client: OpenAI, config: AppConfig, papers: list[Paper]) -> dict[str, str]:
    summaries: dict[str, str] = {}
    for paper in papers:
        prompt = (
            f"标题: {paper.title}\n"
            f"摘要: {paper.abstract}\n\n"
            "请用一句中文概括这篇论文的核心贡献，不超过60字。"
        )
        try:
            summaries[paper.arxiv_id] = _llm_chat(
                client,
                config.llm.model,
                "你是学术论文助手，输出简洁准确的中文一句话总结。",
                prompt,
            )
        except Exception as exc:
            logger.warning("LLM summary failed for %s: %s", paper.arxiv_id, exc)
            summaries[paper.arxiv_id] = _rule_paper_summary(paper)
    return summaries


def _llm_daily_insights(
    client: OpenAI,
    config: AppConfig,
    papers: list[Paper],
    paper_summaries: dict[str, str],
) -> tuple[list[str], list[str]]:
    payload = []
    for paper in papers:
        payload.append(
            {
                "title": paper.title,
                "score": paper.score,
                "summary": paper_summaries.get(paper.arxiv_id, ""),
                "keywords": paper.matched_keywords,
            }
        )

    prompt = (
        "以下是今日筛选出的高质量论文列表（JSON）：\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "请输出 JSON，格式为："
        '{"hotspots": ["热点1", "热点2"], "events": ["大事件1", "大事件2"]}。'
        f"hotspots 给出 {config.summary.hotspot_top_n} 条今日研究热点；"
        f"events 给出 {config.summary.event_top_n} 条值得关注的重要工作。"
        "全部使用中文，条目简洁。"
    )
    raw = _llm_chat(
        client,
        config.llm.model,
        "你是 AI 研究日报编辑，擅长归纳研究热点和重要论文。只输出 JSON。",
        prompt,
    )

    try:
        data = json.loads(raw)
        hotspots = [str(x) for x in data.get("hotspots", [])]
        events = [str(x) for x in data.get("events", [])]
        return hotspots, events
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM JSON response, falling back to rule mode.")
        return _rule_hotspots(papers, config.summary.hotspot_top_n), _rule_events(
            papers, config.summary.event_top_n
        )


def summarize_papers(
    papers: list[Paper],
    config: AppConfig,
    run_date: str | None = None,
) -> DailySummary:
    run_date = run_date or date.today().isoformat()

    if config.llm.enabled:
        logger.info("Using LLM summarizer")
        client = _build_llm_client(config)
        paper_summaries = _llm_paper_summaries(client, config, papers)
        hotspots, events = _llm_daily_insights(client, config, papers, paper_summaries)
    else:
        logger.info("LLM not configured, using rule-based summarizer")
        paper_summaries = {p.arxiv_id: _rule_paper_summary(p) for p in papers}
        hotspots = _rule_hotspots(papers, config.summary.hotspot_top_n)
        events = _rule_events(papers, config.summary.event_top_n)

    for paper in papers:
        paper.summary = paper_summaries.get(paper.arxiv_id, "")

    return DailySummary(
        date=run_date,
        hotspots=hotspots,
        events=events,
        paper_summaries=paper_summaries,
    )
