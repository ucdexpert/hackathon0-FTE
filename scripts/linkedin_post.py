#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Auto Poster - WORKING VERSION

Uses Playwright native clicks (not JavaScript).

Usage:
    python linkedin_post.py "Your post text here"
"""

import sys
import time
import random
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def main():
    if len(sys.argv) < 2:
        print("Usage: python linkedin_post.py \"Your post text\"")
        sys.exit(1)

    if not PLAYWRIGHT_AVAILABLE:
        print("Install: pip install playwright && playwright install chromium")
        sys.exit(1)

    post_text = sys.argv[1]
    session_path = Path('.linkedin_session')
    session_path.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("LINKEDIN AUTO POSTER")
    print("="*60)
    print(f"\nPost: {post_text}\n")
    print("="*60)

    try:
        with sync_playwright() as p:
            # Launch
            print("\n[1/6] Launching browser...")
            browser = p.chromium.launch_persistent_context(
                str(session_path),
                headless=False,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox'],
                timeout=60000
            )
            page = browser.pages[0] if browser.pages else browser.new_page()

            # Login
            print("[2/6] Going to LinkedIn...")
            page.goto('https://www.linkedin.com', wait_until='domcontentloaded', timeout=60000)
            time.sleep(5)

            if 'login' in page.url.lower():
                print("[!] Not logged in. Please login manually...")
                print("[!] Waiting 60 seconds...\n")
                for i in range(60, 0, -1):
                    print(f"\rTime: {i}s", end='', flush=True)
                    time.sleep(1)
                print()

            # Feed
            print("[3/6] Opening feed...")
            page.goto('https://www.linkedin.com/feed', wait_until='domcontentloaded', timeout=60000)
            time.sleep(5)
            print("[OK] Feed loaded!")

            # Click "Start a post" - NATIVE PLAYWRIGHT CLICK
            print("[4/6] Clicking 'Start a post'...")
            
            try:
                # Find the button using text
                start_btn = page.locator('button:has-text("Start a post")').first
                start_btn.wait_for(state='visible', timeout=15000)
                start_btn.scroll_into_view_if_needed()
                time.sleep(2)
                
                # NATIVE CLICK (not JavaScript!)
                start_btn.click()
                print("[OK] 'Start a post' clicked!")
                
                # Wait for modal
                time.sleep(3)
                
            except PlaywrightTimeout:
                print("[!] 'Start a post' button not found")
                print("[!] Trying alternative method...")
                
                # Try direct URL
                page.goto('https://www.linkedin.com/feed/update/urn:li:share:create/', wait_until='domcontentloaded', timeout=60000)
                time.sleep(5)
            
            # Type text
            print("[5/6] Typing post content...")
            time.sleep(2)
            
            # Find editor and type
            typed = False
            
            try:
                # Wait for modal/dialog
                page.wait_for_selector('[role="dialog"]', timeout=10000)
                print("[OK] Modal opened!")
                
                # Find contenteditable div
                editor = page.locator('div[contenteditable="true"]').first
                editor.wait_for(state='visible', timeout=10000)
                
                # Click to focus
                editor.click()
                time.sleep(1)
                
                # Clear existing text
                page.keyboard.press('Control+A')
                time.sleep(0.5)
                page.keyboard.press('Delete')
                time.sleep(0.5)
                
                # Type character by character
                print("[INFO] Typing text...")
                for char in post_text:
                    page.keyboard.type(char)
                    if random.random() < 0.1:  # 10% chance of small pause
                        time.sleep(random.uniform(0.05, 0.15))
                
                print("[OK] Text typed!")
                typed = True
                time.sleep(2)
                
            except Exception as e:
                print(f"[!] Auto-type failed: {e}")
            
            # If auto-type failed, show manual instructions
            if not typed:
                print("\n" + "="*60)
                print("MANUAL COPY-PASTE REQUIRED")
                print("="*60)
                print(f"\nPlease copy this text:\n\n{post_text}\n")
                print("And paste it in LinkedIn post creator\n")
            
            # Wait for Post button click
            print("\n" + "="*60)
            print("CLICK POST BUTTON MANUALLY")
            print("="*60)
            print("\n[INFO] Waiting 90 seconds for you to click 'Post' button...\n")
            
            for i in range(90, 0, -1):
                print(f"\rTime remaining: {i} seconds  ", end='', flush=True)
                time.sleep(1)
            
            print("\n")
            
            # Close
            print("[6/6] Closing browser...")
            browser.close()
            
            print("\n" + "="*60)
            print("[OK] DONE! Check your LinkedIn")
            print("="*60 + "\n")

    except Exception as e:
        print(f"\n[ERROR] {e}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
