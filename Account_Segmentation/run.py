"""Account Segmentation orchestrator (runs after IBM Scraper, before Account
Tiering).

    cd Account_Segmentation
    python3 run.py

Reads DEDUPED_ACCOUNTS (ISC step) as the base and fuzzy-joins the five IBM
install files onto it, then sorts by install-type coverage and writes
SEGMENTED_ACCOUNTS (output/latest.xlsx). Install files that don't exist yet are
simply treated as "no installs" for every account, so this runs fine before all
five IBM sub-scrapers are calibrated.
"""
import logging
import sys

import segment


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    summary = segment.run_segmentation()
    print("\nSegmentation summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    return summary


if __name__ == "__main__":
    main()
