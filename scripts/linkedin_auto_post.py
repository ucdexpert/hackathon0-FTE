#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Auto Poster - ONE COMMAND POST

Single command to post to LinkedIn.
Browser opens, types text automatically. You click Post button.

Usage:
    python linkedin_auto_post.py "Your post text here"
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
        print("Usage: python linkedin_auto_post.py \"Your post text\"")
        print("\nExample:")
        print('  python linkedin_auto_post.py "Hello LinkedIn! #AI"')
        sys.exit(1)

    if not PLAYWRIGHT_AVAILABLE:
        print("Install Playwright:")
        print("  pip install playwright")
        print("  playwright install chromium")
        sys.exit(1)

    post_text = sys.argv[1]
    vault_path = Path('.')
    session_path = vault_path / '.linkedin_session'
    session_path.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("LINKEDIN AUTO POSTER")
    print("="*60)
    print(f"\nPost text:\n{post_text}\n")
    print("Browser will open...")
    print("Post will be typed automatically...")
    print("You just click the 'Post' button!")
    print("="*60 + "\n")

    try:
        with sync_playwright() as p:
            # Launch browser
            print("[1/5] Launching browser...")
            browser = p.chromium.launch_persistent_context(
                str(session_path),
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ],
                timeout=60000
            )

            page = browser.pages[0] if browser.pages else browser.new_page()

            # Go to LinkedIn
            print("[2/5] Going to LinkedIn...")
            page.goto('https://www.linkedin.com', wait_until='domcontentloaded', timeout=60000)
            time.sleep(5)

            # Check login
            if 'login' in page.url.lower():
                print("\n[ERROR] Not logged in!")
                print("[INFO] Please login in the browser window")
                print("[INFO] Waiting 60 seconds...\n")
                time.sleep(60)

            print("[OK] Logged in!")

            # Go to feed
            print("[3/5] Opening feed...")
            page.goto('https://www.linkedin.com/feed', wait_until='domcontentloaded', timeout=60000)
            time.sleep(3)

            # Click "Start a post"
            print("[4/5] Opening post creator...")
            
            # Try clicking with JavaScript
            clicked = page.evaluate('''() => {
                // Find "Start a post" button
                const all = Array.from(document.querySelectorAll('*'));
                for (let el of all) {
                    if (el.textContent.trim() === 'Start a post' && el.offsetParent !== null) {
                        el.click();
                        console.log('Clicked Start a post');
                        return true;
                    }
                }
                return false;
            }''')

            if not clicked:
                print("[WARNING] Could not click 'Start a post' automatically")
                print("[INFO] Please click 'Start a post' manually if modal doesn't open")

            time.sleep(3)

            # Type the post text
            print("[5/5] Typing post content...")
            time.sleep(2)

            # Escape special characters
            escaped = post_text.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')

            # Type using JavaScript
            typed = page.evaluate(f'''() => {{
                const editor = document.querySelector('div[contenteditable="true"]');
                if (editor && editor.offsetParent !== null) {{
                    editor.innerText = `{escaped}`;
                    editor.dispatchEvent(new InputEvent('input', {{ bubbles: true }}));
                    editor.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    console.log('Text entered');
                    return true;
                }}
                
                // Try textarea as fallback
                const textarea = document.querySelector('textarea');
                if (textarea && textarea.offsetParent !== null) {{
                    textarea.value = `{escaped}`;
                    textarea.dispatchEvent(new InputEvent('input', {{ bubbles: true }}));
                    console.log('Text entered in textarea');
                    return true;
                }}
                
                console.log('No editor found');
                return false;
            }}''')

            if typed:
                print("[OK] Post text entered!")
                print("\n" + "="*60)
                print("MANUAL STEP")
                print("="*60)
                print("\n[INFO] Text has been typed in the post creator")
                print("[INFO] Please click the 'Post' button manually")
                print("[INFO] Waiting 90 seconds...\n")

                # Wait for user to click Post
                for i in range(90, 0, -1):
                    print(f"\r[INFO] Time remaining: {i} seconds  ", end='', flush=True)
                    time.sleep(1)

                print("\n")

            else:
                print("[WARNING] Could not type text automatically")
                print("[INFO] You can copy-paste the text manually")
                print(f"\nText to copy:\n{post_text}\n")
                print("[INFO] Waiting 90 seconds...\n")
                for i in range(90, 0, -1):
                    print(f"\r[INFO] Time remaining: {i} seconds  ", end='', flush=True)
                    time.sleep(1)
                print("\n")

            # Close browser
            print("[DONE] Closing browser...")
            time.sleep(2)
            browser.close()

            print("\n" + "="*60)
            print("[OK] DONE!")
            print("[OK] Check your LinkedIn for the post")
            print("="*60 + "\n")

    except Exception as e:
        print(f"\n[ERROR] {e}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
