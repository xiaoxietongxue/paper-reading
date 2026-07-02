from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from paper_reading.models import DailySummary, Paper

logger = logging.getLogger(__name__)


def _reports_dir(output_dir: Path) -> Path:
    return output_dir / "reports"


def generate_report(
    papers: list[Paper],
    summary: DailySummary,
    output_dir: Path,
    run_date: date | None = None,
) -> Path:
    run_date = run_date or date.today()
    report_dir = _reports_dir(output_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{run_date.isoformat()}.md"

    lines = [
        f"# 每日论文日报 {run_date.isoformat()}",
        "",
        "## 概览",
        f"- 入选论文数: {len(papers)}",
        f"- 平均评分: {sum(p.score for p in papers) / len(papers):.2f}" if papers else "- 平均评分: 0",
        "",
        "## 今日研究热点",
    ]

    if summary.hotspots:
        lines.extend(f"- {item}" for item in summary.hotspots)
    else:
        lines.append("- 今日暂无热点数据")

    lines.extend(["", "## 重要大事件"])
    if summary.events:
        lines.extend(f"- {item}" for item in summary.events)
    else:
        lines.append("- 今日暂无重要事件")

    lines.extend(["", "## 论文清单"])
    if not papers:
        lines.append("- 今日未筛选到符合条件的论文")
    else:
        for idx, paper in enumerate(papers, start=1):
            authors = ", ".join(paper.authors[:5])
            if len(paper.authors) > 5:
                authors += " et al."
            lines.extend(
                [
                    f"### {idx}. [{paper.title}]({paper.url})",
                    f"- 作者: {authors}",
                    f"- arXiv ID: {paper.arxiv_id}",
                    f"- 分类: {', '.join(paper.categories)}",
                    f"- 匹配关键词: {', '.join(paper.matched_keywords)}",
                    f"- 评分: {paper.score:.2f}",
                    f"- 一句话提炼: {paper.summary or summary.paper_summaries.get(paper.arxiv_id, '')}",
                    "",
                ]
            )

    with report_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("Report generated: %s", report_path)
    return report_path
