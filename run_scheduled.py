#!/usr/bin/env python3
"""Scheduled runner for Gold Rush Scanner. Runs scans every SCAN_INTERVAL_HOURS."""

import logging
import schedule
import time
from config import SCAN_INTERVAL_HOURS
from scanner import run_full_scan

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("scheduler")


def job():
    try:
        run_full_scan()
    except Exception as e:
        log.error(f"Scan failed: {e}")


if __name__ == "__main__":
    log.info(f"Scheduler started — scanning every {SCAN_INTERVAL_HOURS} hours")
    job()  # Run immediately on start
    schedule.every(SCAN_INTERVAL_HOURS).hours.do(job)
    while True:
        schedule.run_pending()
        time.sleep(60)
