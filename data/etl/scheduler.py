"""
Varuna (ORCA) — INCOIS PFZ Periodic Scheduler Service
Runs every 6 hours to fetch, validate, and cache INCOIS SAMUDRA PFZ advisories
for target coastal states: Maharashtra, Goa, Karnataka, Kerala, Tamil Nadu, Andhra Pradesh, Gujarat.

Usage:
  # Single run (cron job execution):
  python -m data.etl.scheduler --once

  # Continuous daemon service (runs every 6 hours):
  python -m data.etl.scheduler --interval-hours 6

Owner: Jaish
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from datetime import date, datetime

from data.etl.ingest_incois_pfz import run_ingestion

logger = logging.getLogger("varuna.etl.scheduler")


async def scheduled_ingestion_tick(
    dry_run: bool = False,
    force_seed: bool = False,
    cache_dir: str = "data/cache/pfz",
) -> dict:
    """Executes a single periodic ETL tick for INCOIS PFZ data."""
    now_str = datetime.now().isoformat()
    logger.info("Executing scheduled INCOIS PFZ ingestion tick at %s", now_str)

    today_date = date.today()
    try:
        report = await run_ingestion(
            start_date=today_date,
            num_days=1,
            dry_run=dry_run,
            force_seed=force_seed,
            cache_dir=cache_dir,
        )
        logger.info(
            "Scheduled tick completed successfully. Cache summary: %s",
            report.get("cache_summary"),
        )
        return report
    except Exception as exc:
        logger.error("Scheduled INCOIS PFZ ingestion tick failed: %s", exc, exc_info=True)
        return {"status": "error", "error": str(exc), "timestamp": now_str}


async def run_scheduler_daemon(
    interval_hours: float = 6.0,
    dry_run: bool = False,
    force_seed: bool = False,
    cache_dir: str = "data/cache/pfz",
) -> None:
    """Runs a continuous background loop invoking ingestion tick every N hours."""
    interval_seconds = interval_hours * 3600
    logger.info(
        "Starting INCOIS PFZ scheduler daemon (Interval: %.1f hours / %d seconds)",
        interval_hours,
        interval_seconds,
    )

    while True:
        await scheduled_ingestion_tick(
            dry_run=dry_run,
            force_seed=force_seed,
            cache_dir=cache_dir,
        )
        logger.info("Sleeping for %.1f hours until next INCOIS PFZ refresh...", interval_hours)
        await asyncio.sleep(interval_seconds)


def main():
    parser = argparse.ArgumentParser(
        description="Varuna INCOIS PFZ 6-Hour Scheduled Cron Service"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Execute a single ingestion run and exit (useful for cron jobs)",
    )
    parser.add_argument(
        "--interval-hours",
        type=float,
        default=6.0,
        help="Periodic run interval in hours when running as daemon (default: 6.0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and validate features without committing to DB",
    )
    parser.add_argument(
        "--force-seed",
        action="store_true",
        help="Force ingestion of calibrated reference multi-sector advisories",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="data/cache/pfz",
        help="Target local cache directory for GeoJSON output files",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    )

    if args.once:
        logger.info("Running single-shot INCOIS PFZ ingestion task")
        res = asyncio.run(
            scheduled_ingestion_tick(
                dry_run=args.dry_run,
                force_seed=args.force_seed,
                cache_dir=args.cache_dir,
            )
        )
        sys.exit(0 if res.get("status") == "success" else 1)
    else:
        try:
            asyncio.run(
                run_scheduler_daemon(
                    interval_hours=args.interval_hours,
                    dry_run=args.dry_run,
                    force_seed=args.force_seed,
                    cache_dir=args.cache_dir,
                )
            )
        except KeyboardInterrupt:
            logger.info("Scheduler service stopped by user.")


if __name__ == "__main__":
    main()
