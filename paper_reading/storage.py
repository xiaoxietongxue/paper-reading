from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

from paper_reading.models import Paper

logger = logging.getLogger(__name__)


def _papers_dir(output_dir: Path, run_date: date) -> Path:
    return output_dir / "papers" / run_date.isoformat()


def save_papers(papers: list[Paper], output_dir: Path, run_date: date | None = None) -> Path:
    run_date = run_date or date.today()
    target_dir = _papers_dir(output_dir, run_date)
    target_dir.mkdir(parents=True, exist_ok=True)

    for paper in papers:
        paper_path = target_dir / f"{paper.arxiv_id.replace('/', '_')}.json"
        with paper_path.open("w", encoding="utf-8") as f:
            json.dump(paper.to_dict(), f, ensure_ascii=False, indent=2)

    index_path = target_dir / "papers.md"
    lines = [f"# 论文列表 {run_date.isoformat()}", ""]
    for idx, paper in enumerate(papers, start=1):
        authors = ", ".join(paper.authors[:5])
        if len(paper.authors) > 5:
            authors += " et al."
        lines.extend(
            [
                f"## {idx}. {paper.title}",
                f"- arXiv: [{paper.arxiv_id}]({paper.url})",
                f"- 作者: {authors}",
                f"- 分类: {', '.join(paper.categories)}",
                f"- 匹配关键词: {', '.join(paper.matched_keywords)}",
                f"- 评分: {paper.score:.2f}",
                f"- 摘要: {paper.abstract}",
                "",
            ]
        )

    with index_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("Saved %d papers to %s", len(papers), target_dir)
    return target_dir


def load_papers(output_dir: Path, run_date: date) -> list[Paper]:
    target_dir = _papers_dir(output_dir, run_date)
    if not target_dir.exists():
        return []

    papers: list[Paper] = []
    for paper_path in sorted(target_dir.glob("*.json")):
        with paper_path.open("r", encoding="utf-8") as f:
            papers.append(Paper.from_dict(json.load(f)))
    papers.sort(key=lambda p: p.score, reverse=True)
    return papers
