#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Poster - FINAL WORKING VERSION

Fully manual but fast. Just open browser and post.

Usage:
    python lp.py "Your post text"
"""

import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def main():
    if len(sys.argv) < 2:
        print("Usage: python lp.py \"Your post text\"")
        sys.exit(1)

    if not PLAYWRIGHT_AVAILABLE:
        print("Install: pip install playwright && playwright install")
        sys.exit(1)

    post_text = sys.argv[1]
    session_path = Path('.linkedin_session')
    session_path.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*50)
    print("LINKEDIN POSTER")
    print("="*50)
    print(f"\n{post_text}\n")
    print("="*50)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            str(session_path),
            headless=False,
            args=['--disable-blink-features=AutomationControlled'],
            timeout=60000
        )

        page = browser.pages[0]
        page.goto('https://www.linkedin.com', timeout=60000)
        time.sleep(3)

        print("\n[INFO] Browser open. Login if needed.")
        print("[INFO] Press Ctrl+C when done posting.\n")

        # Wait indefinitely
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        browser.close()
        print("\n[OK] Done!")


if __name__ == '__main__':
    main()
