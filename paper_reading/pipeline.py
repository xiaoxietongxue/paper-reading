from __future__ import annotations

import logging
from datetime import date

from paper_reading.config import AppConfig
from paper_reading.fetcher import fetch_papers
from paper_reading.ranker import rank_papers
from paper_reading.report import generate_report
from paper_reading.site_builder import build_site
from paper_reading.storage import save_papers
from paper_reading.summarizer import summarize_papers

logger = logging.getLogger(__name__)


def run_pipeline(config: AppConfig, run_date: date | None = None) -> dict[str, str | int]:
    run_date = run_date or date.today()
    logger.info("Starting daily pipeline for %s", run_date.isoformat())

    papers = fetch_papers(config)
    ranked = rank_papers(papers, config)
    save_papers(ranked, config.output_dir, run_date)
    summary = summarize_papers(ranked, config, run_date.isoformat())
    report_path = generate_report(ranked, summary, config.output_dir, run_date)
    site_path = build_site(config.output_dir, config.site_dir)

    return {
        "date": run_date.isoformat(),
        "fetched": len(papers),
        "selected": len(ranked),
        "report": str(report_path),
        "site": str(site_path),
    }
