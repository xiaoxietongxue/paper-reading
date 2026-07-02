#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from paper_reading.config import load_config
from paper_reading.pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="每日论文总结应用")
    parser.add_argument(
        "--once",
        action="store_true",
        help="立即执行一次抓取与日报生成",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="配置文件路径，默认使用项目根目录 config.yaml",
    )
    return parser.parse_args()


def _run_once(config_path: str | None = None) -> int:
    config = load_config(config_path)
    result = run_pipeline(config)
    logger.info(
        "Pipeline finished: fetched=%s selected=%s report=%s site=%s",
        result["fetched"],
        result["selected"],
        result["report"],
        result["site"],
    )
    return 0


def _run_scheduler(config_path: str | None = None) -> int:
    config = load_config(config_path)
    hour, minute = config.schedule.time.split(":")
    scheduler = BlockingScheduler(timezone=config.schedule.timezone)

    def job() -> None:
        run_pipeline(config)

    scheduler.add_job(
        job,
        CronTrigger(hour=int(hour), minute=int(minute), timezone=config.schedule.timezone),
        id="daily_paper_job",
        replace_existing=True,
    )
    logger.info(
        "Scheduler started. Daily job at %s (%s)",
        config.schedule.time,
        config.schedule.timezone,
    )
    scheduler.start()
    return 0


def main() -> int:
    args = _parse_args()
    root = Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    if args.once:
        return _run_once(args.config)
    return _run_scheduler(args.config)


if __name__ == "__main__":
    raise SystemExit(main())
