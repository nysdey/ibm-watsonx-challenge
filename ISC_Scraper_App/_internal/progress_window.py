"""Tail the scraper log in a small always-on-top Terminal window."""

import subprocess
from pathlib import Path

LOG_FILE = Path(__file__).parent / ".scraper_log.txt"

# Make sure log file exists
LOG_FILE.touch()

# Use osascript to open a small Terminal window that tails the log
applescript = f'''
tell application "Terminal"
    activate
    set w to do script "clear && tail -f '{LOG_FILE}'"
    set bounds of front window to {{30, 30, 580, 330}}
    set custom title of front window to "ISC Scraper Progress"
end tell
'''

subprocess.run(["osascript", "-e", applescript])
