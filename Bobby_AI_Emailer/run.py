"""Bobby, the AI Emailer — CLI / dashboard entry point.

    cd Bobby_AI_Emailer
    python3 run.py --cadence "Targeted Outreach Cadence 4"

Reads the chosen Salesloft cadence's email steps + enrolled people and writes a
personalized email per person (by cadence day, title, company). Drafts are saved to
output/ (and shown in the dashboard's Bobby view); nothing is sent.
"""
import argparse
import logging
import sys
from datetime import datetime

import config


def _setup_logging():
    log_path = config.LOG_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler(sys.stdout)],
    )
    return log_path


def main():
    parser = argparse.ArgumentParser(description="Bobby, the AI Emailer")
    parser.add_argument("--cadence", required=True, help="Salesloft cadence name to write emails for.")
    args = parser.parse_args()

    log_path = _setup_logging()
    logger = logging.getLogger("run")
    logger.info("Bobby starting for cadence %r. Log: %s", args.cadence, log_path)

    import bobby
    try:
        summary = bobby.run_bobby(args.cadence)
    except bobby.SessionExpired as e:
        logger.error("%s", e)
        sys.exit(2)
    except bobby.CadenceNotFound as e:
        logger.error("%s", e)
        sys.exit(3)
    except ImportError as e:
        logger.error("Playwright not installed (%s) — run: pip install playwright && "
                     "playwright install firefox", e)
        sys.exit(1)
    except Exception as e:
        logger.exception("Bobby failed: %s", e)
        sys.exit(1)

    logger.info("Bobby complete: %s", summary)


if __name__ == "__main__":
    main()
