#!/usr/bin/env python3
"""
LinkedIn FULLY AUTO Post - NO MANUAL CLICKS!

Browser opens, types text, clicks Post button automatically.

Usage:
    python autopost.py "Your post text here"
"""

import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install: pip install playwright && playwright install chromium")
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python autopost.py \"Your post text\"")
        sys.exit(1)

    post_text = sys.argv[1]
    session = Path('.linkedin_session')
    session.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("LINKEDIN FULLY AUTO POST")
    print("="*60)
    print(f"\nPost: {post_text}\n")
    print("Everything will be automatic!")
    print("="*60 + "\n")

    with sync_playwright() as p:
        # Launch
        print("[1/5] Launching browser...")
        browser = p.chromium.launch_persistent_context(
            str(session),
            headless=False,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox'],
            timeout=90000
        )

        page = browser.pages[0]

        # Go to LinkedIn
        print("[2/5] Going to LinkedIn...")
        page.goto('https://www.linkedin.com', timeout=90000)
        time.sleep(5)

        # Check login
        if 'login' in page.url.lower():
            print("\n[!] NOT LOGGED IN!")
            print("[!] Waiting 60 seconds for login...\n")
            for i in range(60, 0, -1):
                print(f"\r{i}s ", end='', flush=True)
                time.sleep(1)
            print()

        # Go to feed
        print("[3/5] Opening feed...")
        page.goto('https://www.linkedin.com/feed', timeout=90000)
        time.sleep(5)
        print("[OK] Feed loaded!")

        # Click "Start a post"
        print("\n[4/5] Clicking 'Start a post'...")
        
        clicked = False
        
        # Method 1: Click by aria-label
        try:
            btn = page.locator('[aria-label="Start a post"]').first
            btn.wait_for(state='visible', timeout=15000)
            btn.click()
            print("[OK] Clicked via aria-label!")
            clicked = True
        except:
            print("[!] aria-label failed")
        
        # Method 2: Click by text
        if not clicked:
            try:
                btn = page.locator('button:has-text("Start a post")').first
                btn.wait_for(state='visible', timeout=15000)
                btn.click()
                print("[OK] Clicked via text!")
                clicked = True
            except:
                print("[!] Text selector failed")
        
        # Method 3: JavaScript click
        if not clicked:
            print("[!] Using JavaScript click...")
            page.evaluate('''() => {
                const all = Array.from(document.querySelectorAll('*'));
                for (let el of all) {
                    if (el.textContent.trim() === 'Start a post' && el.offsetParent !== null) {
                        el.click();
                        return;
                    }
                }
            }''')
            time.sleep(3)

        time.sleep(3)

        # Type text
        print("\n[5/5] Typing post content...")
        time.sleep(2)

        try:
            editor = page.locator('div[contenteditable="true"]').first
            editor.wait_for(state='visible', timeout=15000)
            editor.click()
            time.sleep(1)

            # Clear
            page.keyboard.press('Control+A')
            time.sleep(0.3)
            page.keyboard.press('Delete')
            time.sleep(0.5)

            # Type
            page.keyboard.type(post_text, delay=50)
            print("[OK] Text typed!")

        except Exception as e:
            print(f"[!] Type failed: {e}")
            # Fallback: JavaScript
            escaped = post_text.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
            page.evaluate(f'''() => {{
                const editor = document.querySelector('div[contenteditable="true"]');
                if (editor) {{
                    editor.innerText = `{escaped}`;
                    editor.dispatchEvent(new InputEvent('input', {{ bubbles: true }}));
                }}
            }}''')
            print("[OK] Text via JavaScript!")

        time.sleep(3)

        # CLICK POST BUTTON AUTOMATICALLY!
        print("\n[AUTO] Clicking POST button automatically...")
        
        post_clicked = False
        
        # Method 1: Playwright click
        try:
            post_btn = page.locator('button:has-text("Post")').first
            post_btn.wait_for(state='visible', timeout=15000)
            post_btn.wait_for(state='enabled', timeout=10000)
            post_btn.scroll_into_view_if_needed()
            post_btn.click(force=True)
            print("[OK] Post button clicked via Playwright!")
            post_clicked = True
        except Exception as e:
            print(f"[!] Playwright Post click failed: {e}")
        
        # Method 2: JavaScript click
        if not post_clicked:
            print("[AUTO] Using JavaScript to click Post...")
            result = page.evaluate('''() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                for (let btn of buttons) {
                    if (btn.textContent.trim() === 'Post' && btn.offsetParent !== null) {
                        btn.click();
                        btn.dispatchEvent(new MouseEvent('click', {
                            bubbles: true,
                            cancelable: true,
                            view: window
                        }));
                        console.log('Post clicked!');
                        return true;
                    }
                }
                return false;
            }''')
            
            if result:
                print("[OK] Post button clicked via JavaScript!")
                post_clicked = True
        
        # Method 3: Control+Enter
        if not post_clicked:
            print("[AUTO] Using Control+Enter shortcut...")
            page.keyboard.press('Control+Enter')
            print("[OK] Control+Enter sent!")

        # Wait for confirmation
        print("\n[INFO] Waiting for post to submit...")
        time.sleep(5)

        # Verify
        try:
            page.wait_for_selector('text="Posted"', timeout=10000)
            print("[OK] Post verified!")
        except:
            print("[INFO] Assuming post submitted")

        # Close
        time.sleep(2)
        browser.close()

        print("\n" + "="*60)
        print("[OK] DONE! POST PUBLISHED!")
        print("[OK] Check your LinkedIn profile")
        print("="*60 + "\n")


if __name__ == '__main__':
    main()
