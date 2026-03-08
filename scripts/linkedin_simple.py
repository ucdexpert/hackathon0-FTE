#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Auto Poster - SIMPLE WORKING VERSION

Opens LinkedIn, you manually click "Start a post", text auto-types.

Usage:
    python linkedin_simple.py "Your post text here"
"""

import sys
import time
import random
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def main():
    if len(sys.argv) < 2:
        print("Usage: python linkedin_simple.py \"Your post text\"")
        sys.exit(1)

    if not PLAYWRIGHT_AVAILABLE:
        print("Install: pip install playwright && playwright install chromium")
        sys.exit(1)

    post_text = sys.argv[1]
    session_path = Path('.linkedin_session')
    session_path.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("LINKEDIN AUTO POSTER (SIMPLE)")
    print("="*60)
    print(f"\nPost: {post_text}\n")
    print("INSTRUCTIONS:")
    print("1. Browser will open")
    print("2. Click 'Start a post' button manually")
    print("3. Text will auto-type")
    print("4. Click 'Post' button")
    print("="*60 + "\n")

    try:
        with sync_playwright() as p:
            # Launch
            print("[1/5] Launching browser...")
            browser = p.chromium.launch_persistent_context(
                str(session_path),
                headless=False,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox'],
                timeout=60000
            )
            page = browser.pages[0] if browser.pages else browser.new_page()

            # Go to LinkedIn
            print("[2/5] Going to LinkedIn...")
            page.goto('https://www.linkedin.com', wait_until='domcontentloaded', timeout=60000)
            time.sleep(5)

            # Check login
            if 'login' in page.url.lower():
                print("\n[!] NOT LOGGED IN!")
                print("[!] Please login in the browser")
                print("[!] Waiting 60 seconds...\n")
                for i in range(60, 0, -1):
                    print(f"\r{i}s ", end='', flush=True)
                    time.sleep(1)
                print()

            # Go to feed
            print("[3/5] Opening LinkedIn feed...")
            page.goto('https://www.linkedin.com/feed', wait_until='domcontentloaded', timeout=60000)
            time.sleep(5)

            print("\n" + "="*60)
            print("MANUAL STEP: Click 'Start a post' button")
            print("="*60)
            print("\n[INFO] Waiting 30 seconds for you to click 'Start a post'...\n")

            # Wait for user to click "Start a post"
            for i in range(30, 0, -1):
                print(f"\rTime: {i}s  ", end='', flush=True)
                time.sleep(1)
            print()

            # Check if modal opened
            modal_open = page.evaluate('''() => {
                const modal = document.querySelector('[role="dialog"]');
                const editor = document.querySelector('div[contenteditable="true"]');
                return (modal !== null) || (editor !== null);
            }''')

            if not modal_open:
                print("\n[!] Modal not detected. Trying direct URL...")
                page.goto('https://www.linkedin.com/feed/update/urn:li:share:create/', wait_until='domcontentloaded', timeout=60000)
                time.sleep(5)

            # Type text
            print("[4/5] Typing post content...")
            time.sleep(2)

            typed = False

            try:
                # Find editor
                editor = page.locator('div[contenteditable="true"]').first
                editor.wait_for(state='visible', timeout=10000)
                editor.click()
                time.sleep(1)

                # Clear
                page.keyboard.press('Control+A')
                time.sleep(0.3)
                page.keyboard.press('Delete')
                time.sleep(0.5)

                # Type with delays
                print("[INFO] Typing...")
                for char in post_text:
                    page.keyboard.type(char)
                    if random.random() < 0.1:
                        time.sleep(random.uniform(0.05, 0.15))

                print("[OK] Text typed!")
                typed = True
                time.sleep(2)

            except Exception as e:
                print(f"[!] Auto-type failed: {e}")

            if not typed:
                print("\n" + "="*60)
                print("MANUAL COPY-PASTE")
                print("="*60)
                print(f"\nCopy this text:\n\n{post_text}\n")
                print("Paste it in LinkedIn and click Post\n")

            # Wait for Post button click
            print("\n" + "="*60)
            print("CLICK 'POST' BUTTON MANUALLY")
            print("="*60)
            print("\n[INFO] Waiting 60 seconds...\n")

            for i in range(60, 0, -1):
                print(f"\rTime: {i}s  ", end='', flush=True)
                time.sleep(1)
            print()

            # Close
            print("[5/5] Closing browser...")
            browser.close()

            print("\n" + "="*60)
            print("[OK] DONE!")
            print("="*60 + "\n")

    except Exception as e:
        print(f"\n[ERROR] {e}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
