#!/usr/bin/env python3
"""
Simple LinkedIn Poster - Opens browser visibly for reliable posting.
Usage: python simple_post.py "Your post text here"
"""

import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install: pip install playwright && playwright install chromium")
    sys.exit(1)

VAULT = Path(__file__).parent.parent
SESSION = VAULT / ".linkedin_session"
LOGS = VAULT / "Logs"
LOGS.mkdir(parents=True, exist_ok=True)

def post(text):
    print(f"\nPosting: {text[:60]}...\n")
    
    with sync_playwright() as p:
        # Launch visible browser
        browser = p.chromium.launch_persistent_context(
            str(SESSION),
            headless=False,  # Visible!
            viewport={"width": 1280, "height": 800},
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        # Go to feed
        print("1. Opening LinkedIn...")
        page.goto("https://www.linkedin.com/feed/")
        time.sleep(5)
        
        # Click "Start a post"
        print("2. Clicking 'Start a post'...")
        page.evaluate("""
            () => {
                const btn = Array.from(document.querySelectorAll('button'))
                    .find(b => b.textContent.includes('Start a post'));
                if (btn) btn.click();
            }
        """)
        time.sleep(3)
        
        # Find editor and type
        print("3. Typing content... (watch the browser!)")
        page.evaluate("""
            (text) => {
                const editor = document.querySelector('div[contenteditable="true"]');
                if (editor) {
                    editor.focus();
                    editor.innerText = text;
                }
            }
        """, text)
        time.sleep(2)
        
        # Click Post button
        print("4. Clicking 'Post'...")
        page.evaluate("""
            () => {
                const btn = Array.from(document.querySelectorAll('button'))
                    .find(b => b.textContent.trim() === 'Post' && !b.disabled);
                if (btn) btn.click();
            }
        """)
        
        # Screenshot
        time.sleep(5)
        screenshot = LOGS / f"post_{int(time.time())}.png"
        page.screenshot(path=str(screenshot))
        print(f"\n✓ Posted! Screenshot: {screenshot}\n")
        
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_post.py \"Your post text\"")
        sys.exit(1)
    post(" ".join(sys.argv[1:]))
