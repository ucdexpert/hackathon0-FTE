# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# LinkedIn Watcher/Poster - Monitor and post to LinkedIn.

# WARNING: This uses LinkedIn automation which may violate LinkedIn's Terms of Service.
# Use at your own risk and only for personal accounts.

# Usage:
#     python linkedin_watcher.py /path/to/vault --authenticate  # First time
#     python linkedin_watcher.py /path/to/vault --post "Hello LinkedIn!"
#     python linkedin_watcher.py /path/to/vault --check  # Check for notifications
# """

# import sys
# import time
# import logging
# import argparse
# import json
# from pathlib import Path
# from datetime import datetime
# from typing import List, Dict, Optional

# try:
#     from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
# except ImportError:
#     print("Missing dependencies. Install with:")
#     print("  pip install playwright")
#     print("  playwright install chromium")
#     sys.exit(1)

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )


# class LinkedInWatcher:
#     """Monitor and post to LinkedIn using browser automation."""
    
#     def __init__(self, vault_path: str, session_path: str,
#                  check_interval: int = 300, keywords: List[str] = None):
#         """
#         Initialize LinkedIn Watcher.
        
#         Args:
#             vault_path: Path to Obsidian vault
#             session_path: Path to save browser session
#             check_interval: Seconds between checks (default: 300 = 5 min)
#             keywords: Keywords to monitor in notifications
#         """
#         self.vault_path = Path(vault_path)
#         self.session_path = Path(session_path)
#         self.check_interval = check_interval
#         self.keywords = keywords or ['comment', 'message', 'connection', 'job']
        
#         self.needs_action = self.vault_path / 'Needs_Action'
#         self.done = self.vault_path / 'Done'
        
#         # Ensure directories exist
#         self.needs_action.mkdir(parents=True, exist_ok=True)
#         self.done.mkdir(parents=True, exist_ok=True)
#         self.session_path.mkdir(parents=True, exist_ok=True)
        
#         self.logger = logging.getLogger(self.__class__.__name__)
#         self.processed_notifications = set()
    
#     def authenticate(self) -> bool:
#         """
#         Authenticate with LinkedIn (save session).
        
#         Returns:
#             True if successful
#         """
#         try:
#             with sync_playwright() as p:
#                 browser = p.chromium.launch_persistent_context(
#                     str(self.session_path),
#                     headless=False,  # Show browser for login
#                     args=['--disable-blink-features=AutomationControlled']
#                 )
                
#                 page = browser.pages[0] if browser.pages else browser.new_page()
#                 page.goto('https://www.linkedin.com/login')
                
#                 self.logger.info("Please log in to LinkedIn manually...")
#                 self.logger.info("Session will be saved for future use.")
                
#                 # Wait for user to log in (max 5 minutes)
#                 try:
#                     page.wait_for_url('https://www.linkedin.com/feed/*', timeout=300000)
#                     self.logger.info("Login detected!")
#                     time.sleep(2)  # Let session fully load
#                     browser.close()
#                     return True
#                 except PlaywrightTimeout:
#                     self.logger.warning("Login timeout. Try again.")
#                     browser.close()
#                     return False
                    
#         except Exception as e:
#             self.logger.error(f"Authentication error: {e}")
#             return False
    
#     def check_notifications(self) -> List[Dict]:
#         """
#         Check LinkedIn notifications.
        
#         Returns:
#             List of new notifications
#         """
#         notifications = []
        
#         try:
#             with sync_playwright() as p:
#                 browser = p.chromium.launch_persistent_context(
#                     str(self.session_path),
#                     headless=True,
#                     args=[
#                         '--disable-blink-features=AutomationControlled',
#                         '--disable-dev-shm-usage',
#                         '--no-sandbox'
#                     ],
#                     viewport={'width': 1280, 'height': 720}
#                 )
                
#                 page = browser.pages[0] if browser.pages else browser.new_page()
                
#                 # Navigate to notifications
#                 self.logger.debug("Navigating to LinkedIn notifications...")
#                 page.goto('https://www.linkedin.com/notifications/', wait_until='networkidle')
                
#                 # Wait for notifications list
#                 try:
#                     page.wait_for_selector('[data-test-id="notification-list"]', timeout=15000)
#                     self.logger.debug("Notifications loaded")
#                 except PlaywrightTimeout:
#                     self.logger.warning("Notifications did not load. May need to re-authenticate.")
#                     browser.close()
#                     return []
                
#                 # Small delay for content to load
#                 time.sleep(2)
                
#                 # Find notification items
#                 try:
#                     notification_items = page.query_selector_all('[data-test-id="notification-item"]')
#                     self.logger.debug(f"Found {len(notification_items)} notifications")
                    
#                     for item in notification_items[:10]:  # Limit to 10
#                         try:
#                             text = item.inner_text(timeout=2000)
#                             notification_id = item.get_attribute('id') or str(hash(text))
                            
#                             # Check if already processed
#                             if notification_id not in self.processed_notifications:
#                                 # Check for keywords
#                                 text_lower = text.lower()
#                                 matched = [kw for kw in self.keywords if kw in text_lower]
                                
#                                 if matched:
#                                     notifications.append({
#                                         'id': notification_id,
#                                         'text': text,
#                                         'keywords': matched,
#                                         'timestamp': datetime.now().isoformat()
#                                     })
#                                     self.processed_notifications.add(notification_id)
#                                     self.logger.info(f"Found notification with keywords: {matched}")
#                         except Exception:
#                             continue
                            
#                 except Exception as e:
#                     self.logger.error(f"Error finding notifications: {e}")
                
#                 browser.close()
                
#         except Exception as e:
#             self.logger.error(f"Error checking notifications: {e}")
        
#         return notifications
    
#     def post_update(self, content: str, hashtags: List[str] = None,
#                     screenshot: bool = True) -> Dict:
#         """
#         Post update to LinkedIn.
        
#         Args:
#             content: Post content
#             hashtags: List of hashtags (without #)
#             screenshot: Take screenshot after posting
            
#         Returns:
#             Dict with post result
#         """
#         result = {'status': 'unknown', 'content': content}
        
#         try:
#             with sync_playwright() as p:
#                 browser = p.chromium.launch_persistent_context(
#                     str(self.session_path),
#                     headless=True,
#                     args=[
#                         '--disable-blink-features=AutomationControlled',
#                         '--disable-dev-shm-usage',
#                         '--no-sandbox'
#                     ],
#                     viewport={'width': 1280, 'height': 720}
#                 )
                
#                 page = browser.pages[0] if browser.pages else browser.new_page()
                
#                 # Navigate to feed
#                 self.logger.debug("Navigating to LinkedIn feed...")
#                 page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
#                 time.sleep(5)  # Wait for dynamic content
                
#                 # Wait for post creation box
#                 try:
#                     page.wait_for_selector('[aria-label="Start a post"]', timeout=20000)
#                     self.logger.debug("Feed loaded")
#                 except PlaywrightTimeout:
#                     self.logger.warning("'Start a post' not found, trying alternative...")
#                     # Try direct navigation to post creator
#                     page.goto('https://www.linkedin.com/feed/update/urn:li:share:create/', wait_until='domcontentloaded', timeout=30000)
#                     time.sleep(3)
                
#                 # Small delay to appear human
#                 time.sleep(2)
                
#                 # Click "Start a post"
#                 self.logger.debug("Clicking 'Start a post'...")
#                 page.click('[aria-label="Start a post"]')
                
#                 # Wait for post dialog - try multiple selectors
#                 time.sleep(3)
                
#                 # Find editor - try multiple approaches
#                 editor_found = False
                
#                 # Approach 1: .ql-editor (old LinkedIn)
#                 try:
#                     page.wait_for_selector('.ql-editor', timeout=5000)
#                     editor_found = True
#                     self.logger.debug("Found editor via .ql-editor")
#                 except PlaywrightTimeout:
#                     pass
                
#                 # Approach 2: contenteditable div (new LinkedIn)
#                 if not editor_found:
#                     try:
#                         page.wait_for_selector('div[contenteditable="true"][role="textbox"]', timeout=5000)
#                         editor_found = True
#                         self.logger.debug("Found editor via contenteditable")
#                     except PlaywrightTimeout:
#                         pass
                
#                 # Approach 3: Any contenteditable
#                 if not editor_found:
#                     try:
#                         page.wait_for_selector('div[contenteditable="true"]', timeout=5000)
#                         editor_found = True
#                         self.logger.debug("Found editor via generic contenteditable")
#                     except PlaywrightTimeout:
#                         pass
                
#                 if not editor_found:
#                     self.logger.warning("Editor not found, continuing anyway...")
                
#                 time.sleep(1)
                
#                 # Prepare content with hashtags
#                 full_content = content
#                 if hashtags:
#                     hashtag_str = ' '.join([f'#{tag}' for tag in hashtags])
#                     full_content = f"{content}\n\n{hashtag_str}"
                
#                 # Type content
#                 self.logger.debug("Typing content...")
                
#                 # Find editor element
#                 editor = None
                
#                 # Try multiple selectors
#                 selectors = [
#                     '.ql-editor',
#                     'div[contenteditable="true"][role="textbox"]',
#                     'div[contenteditable="true"]'
#                 ]
                
#                 for selector in selectors:
#                     try:
#                         editor = page.locator(selector).first
#                         editor.wait_for(state='visible', timeout=5000)
#                         self.logger.debug(f"Using editor: {selector}")
#                         break
#                     except:
#                         continue
                
#                 if editor:
#                     # Fill content
#                     editor.fill(full_content)
#                     time.sleep(2)
#                     self.logger.info("Content typed successfully")
#                 else:
#                     self.logger.warning("Could not find editor, trying keyboard...")
#                     # Fallback: keyboard type
#                     page.keyboard.type(full_content, delay=50)
#                     time.sleep(2)
                
#                 # Click "Post" button
#                 self.logger.debug("Clicking 'Post'...")
                
#                 # Method 1: Playwright click
#                 post_clicked = False
#                 try:
#                     post_button = page.locator('button:has-text("Post")').first
#                     post_button.wait_for(state='enabled', timeout=10000)
                    
#                     # Scroll into view
#                     try:
#                         post_button.scroll_into_view_if_needed(timeout=5000)
#                     except:
#                         pass
                    
#                     # Click with force
#                     post_button.click(force=True, timeout=10000)
#                     post_clicked = True
#                     self.logger.info("Post button clicked (Playwright)")
                    
#                 except Exception as e:
#                     self.logger.warning(f"Playwright click failed: {e}")
                
#                 # Method 2: JavaScript click (fallback)
#                 if not post_clicked:
#                     try:
#                         result = page.evaluate('''() => {
#                             const buttons = Array.from(document.querySelectorAll('button'));
#                             for (let btn of buttons) {
#                                 if (btn.textContent.trim() === 'Post' && btn.offsetParent !== null) {
#                                     btn.click();
#                                     console.log('Post clicked via JS');
#                                     return true;
#                                 }
#                             }
#                             return false;
#                         }''')
                        
#                         if result:
#                             post_clicked = True
#                             self.logger.info("Post button clicked (JavaScript)")
                            
#                     except Exception as e:
#                         self.logger.warning(f"JavaScript click failed: {e}")
                
#                 # Method 3: Control+Enter (final fallback)
#                 if not post_clicked:
#                     self.logger.info("Using Control+Enter shortcut...")
#                     page.keyboard.press('Control+Enter')
#                     time.sleep(3)
#                     self.logger.info("Sent Control+Enter")
                
#                 # Wait for success toast
#                 try:
#                     page.wait_for_selector('.post-updated-toast, .toast', timeout=10000)
#                     self.logger.info("Post successful!")
#                     result['status'] = 'posted'
#                     result['timestamp'] = datetime.now().isoformat()
#                 except PlaywrightTimeout:
#                     self.logger.warning("Post confirmation not detected")
#                     result['status'] = 'posted'  # Assume success since Control+Enter was sent
#                     result['timestamp'] = datetime.now().isoformat()
                
#                 # Take screenshot
#                 if screenshot and result['status'] == 'posted':
#                     screenshot_path = self.done / f'linkedin_{int(time.time())}.png'
#                     page.screenshot(path=str(screenshot_path))
#                     result['screenshot'] = str(screenshot_path)
#                     self.logger.info(f"Screenshot saved: {screenshot_path.name}")
                
#                 browser.close()
                
#         except Exception as e:
#             self.logger.error(f"Error posting: {e}")
#             result['status'] = 'error'
#             result['error'] = str(e)
        
#         return result
    
#     def create_notification_action_file(self, notification: Dict) -> Path:
#         """Create action file for important notification."""
#         timestamp = datetime.now().isoformat()
#         filename = f'LINKEDIN_NOTIF_{int(time.time())}.md'
        
#         content = f'''---
# type: linkedin_notification
# received: {timestamp}
# keywords: {', '.join(notification['keywords'])}
# status: pending
# ---

# # LinkedIn Notification

# ## Content

# {notification['text']}

# ## Keywords Matched

# {', '.join(notification['keywords'])}

# ## Suggested Actions

# - [ ] Review notification
# - [ ] Respond if needed (comment/message)
# - [ ] Check LinkedIn for context
# - [ ] Archive after processing

# ---
# *Generated by LinkedIn Watcher v0.1 (Silver Tier)*
# '''
#         filepath = self.needs_action / filename
#         filepath.write_text(content)
        
#         self.logger.info(f"Created notification action file: {filename}")
#         return filepath
    
#     def run(self):
#         """Main loop - continuously check for notifications."""
#         self.logger.info('=' * 50)
#         self.logger.info('LinkedIn Watcher starting')
#         self.logger.info(f'Vault: {self.vault_path}')
#         self.logger.info(f'Session: {self.session_path}')
#         self.logger.info(f'Check interval: {self.check_interval}s')
#         self.logger.info(f'Keywords: {self.keywords}')
#         self.logger.info('=' * 50)
        
#         # Check if session exists
#         if not any(self.session_path.iterdir()):
#             self.logger.warning("No session data found.")
#             self.logger.warning("Run with --authenticate first to log in.")
#             return
        
#         self.logger.info("Starting notification monitoring...")
        
#         while True:
#             try:
#                 notifications = self.check_notifications()
                
#                 for notif in notifications:
#                     self.create_notification_action_file(notif)
                    
#             except Exception as e:
#                 self.logger.error(f"Error in check loop: {e}")
            
#             time.sleep(self.check_interval)


# def main():
#     """Main entry point."""
#     parser = argparse.ArgumentParser(description='LinkedIn Watcher/Poster')
#     parser.add_argument('vault_path', help='Path to Obsidian vault')
#     parser.add_argument('--session', '-s', help='Path to session folder')
#     parser.add_argument('--interval', '-i', type=int, default=300,
#                        help='Check interval in seconds (default: 300)')
#     parser.add_argument('--keywords', '-k', nargs='+',
#                        help='Keywords to monitor')
#     parser.add_argument('--authenticate', '-a', action='store_true',
#                        help='Run authentication flow')
#     parser.add_argument('--post', '-p', help='Post content to LinkedIn')
#     parser.add_argument('--hashtags', '-H', nargs='+', default=['business', 'tech'],
#                        help='Hashtags for post (default: business tech)')
#     parser.add_argument('--check', '-c', action='store_true',
#                        help='Check notifications once')
#     parser.add_argument('--config', help='Path to config JSON file')
    
#     args = parser.parse_args()
    
#     vault_path = Path(args.vault_path)
#     if not vault_path.exists():
#         print(f"Error: Vault path does not exist: {vault_path}")
#         sys.exit(1)
    
#     # Load config
#     config = {}
#     if args.config:
#         config_path = Path(args.config)
#         if config_path.exists():
#             config = json.loads(config_path.read_text())
    
#     # Session path
#     session_path = Path(args.session) if args.session else config.get('session_path', vault_path / '.linkedin_session')
    
#     # Create watcher
#     watcher = LinkedInWatcher(
#         str(vault_path),
#         str(session_path),
#         args.interval or config.get('check_interval', 300),
#         args.keywords or config.get('keywords', ['comment', 'message', 'connection', 'job'])
#     )
    
#     if args.authenticate:
#         print("Starting LinkedIn authentication...")
#         print("A browser window will open. Log in to LinkedIn.")
#         print("Session will be saved for future use.")
#         print()
#         if watcher.authenticate():
#             print("")
#             print("Authentication successful!")
#             print("You can now post or check notifications.")
#         else:
#             print("")
#             print("Authentication failed")
#             sys.exit(1)
    
#     elif args.post:
#         print(f"Posting to LinkedIn: {args.post[:50]}...")
#         result = watcher.post_update(args.post, args.hashtags)
#         print(f"Result: {result['status']}")
#         if result.get('screenshot'):
#             print(f"Screenshot: {result['screenshot']}")
    
#     elif args.check:
#         print("Checking notifications...")
#         notifications = watcher.check_notifications()
#         if notifications:
#             print(f"Found {len(notifications)} new notifications:")
#             for n in notifications:
#                 print(f"  - {n['keywords']}: {n['text'][:50]}...")
#         else:
#             print("No new notifications.")
    
#     else:
#         # Run continuous watcher
#         watcher.run()


# if __name__ == '__main__':
#     main()









#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class LinkedInWatcher:

    def __init__(self, vault_path: str, session_path: str, check_interval: int = 300,
                 keywords: List[str] = None):

        self.vault_path = Path(vault_path)
        self.session_path = Path(session_path)

        self.check_interval = check_interval
        self.keywords = keywords or ["comment", "message", "connection", "job"]

        self.needs_action = self.vault_path / "Needs_Action"
        self.done = self.vault_path / "Done"

        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.done.mkdir(parents=True, exist_ok=True)
        self.session_path.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger("LinkedInWatcher")
        self.processed_notifications = set()

    # ================= AUTH ================= #

    def authenticate(self):

        with sync_playwright() as p:

            browser = p.chromium.launch_persistent_context(
                str(self.session_path),
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )

            page = browser.pages[0] if browser.pages else browser.new_page()

            page.goto("https://www.linkedin.com/login")

            print("\nLogin manually in browser...")
            print("Session will save automatically.\n")

            page.wait_for_url("https://www.linkedin.com/feed/*", timeout=300000)

            print("Login successful")

            browser.close()

    # ================= POST ================= #

    def post_update(self, content: str, hashtags: List[str] = None,
                    screenshot: bool = True):

        if hashtags:
            content += "\n\n" + " ".join([f"#{h}" for h in hashtags])

        with sync_playwright() as p:

            browser = p.chromium.launch_persistent_context(
                str(self.session_path),
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )

            page = browser.pages[0] if browser.pages else browser.new_page()

            self.logger.info("Opening LinkedIn feed")

            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")

            # Wait for feed UI
            time.sleep(5)

            # ========== OPEN POST BOX ========== #

            post_buttons = [
                'div.share-box-feed-entry__trigger',
                'button:has-text("Start a post")',
                'button:has-text("Post")',
                '[aria-label*="post"]'
            ]

            clicked = False

            for selector in post_buttons:
                try:
                    page.locator(selector).first.click(timeout=8000)
                    clicked = True
                    break
                except:
                    continue

            if not clicked:
                raise Exception("Cannot find Start Post button")

            time.sleep(3)

            # ========== FIND EDITOR ========== #

            editor = None

            editor_selectors = [
                'div[contenteditable="true"][role="textbox"]',
                '.ql-editor',
                'div[contenteditable="true"]'
            ]

            for selector in editor_selectors:
                try:
                    editor = page.locator(selector).first
                    editor.wait_for(state="visible", timeout=8000)
                    break
                except:
                    continue

            if not editor:
                raise Exception("Editor not found")

            # Type content (human style)
            editor.click()
            page.keyboard.type(content, delay=40)

            time.sleep(2)

            # ========== CLICK POST ========== #

            post_clicked = False

            post_buttons = [
                'button:has-text("Post")',
                'button:has-text("Share")',
                'button[aria-label*="Post"]'
            ]

            for selector in post_buttons:
                try:
                    btn = page.locator(selector).first
                    btn.click(timeout=8000)
                    post_clicked = True
                    break
                except:
                    continue

            if not post_clicked:
                page.keyboard.press("Control+Enter")

            self.logger.info("Post submitted")

            time.sleep(6)

            # Screenshot proof
            if screenshot:
                shot = self.done / f"linkedin_{int(time.time())}.png"
                page.screenshot(path=str(shot))
                self.logger.info(f"Screenshot saved {shot}")

            browser.close()

    # ================= NOTIFICATIONS ================= #

    def check_notifications(self) -> List[Dict]:

        notifications = []

        with sync_playwright() as p:

            browser = p.chromium.launch_persistent_context(
                str(self.session_path),
                headless=True
            )

            page = browser.pages[0] if browser.pages else browser.new_page()

            page.goto("https://www.linkedin.com/notifications/",
                      wait_until="domcontentloaded")

            time.sleep(5)

            try:
                items = page.query_selector_all(
                    '[data-test-id="notification-item"]'
                )

                for item in items[:10]:

                    try:
                        text = item.inner_text()

                        notif_id = hash(text)

                        if notif_id not in self.processed_notifications:

                            lower = text.lower()

                            matched = [
                                k for k in self.keywords if k in lower
                            ]

                            if matched:

                                notifications.append({
                                    "id": notif_id,
                                    "text": text,
                                    "keywords": matched,
                                    "timestamp": datetime.now().isoformat()
                                })

                                self.processed_notifications.add(notif_id)

                    except:
                        continue

            except Exception as e:
                self.logger.error(e)

            browser.close()

        return notifications

    # ================= RUN LOOP ================= #

    def run(self):

        if not any(self.session_path.iterdir()):
            print("Run with --authenticate first")
            return

        while True:

            try:
                notes = self.check_notifications()

                for n in notes:
                    self.create_notification_action_file(n)

            except Exception as e:
                self.logger.error(e)

            time.sleep(self.check_interval)

    # ================= FILE GENERATOR ================= #

    def create_notification_action_file(self, notification: Dict):

        filename = f"LINKEDIN_NOTIF_{int(time.time())}.md"

        content = f"""
---
type: linkedin_notification
received: {notification['timestamp']}
keywords: {', '.join(notification['keywords'])}
---

# LinkedIn Notification

{notification['text']}
"""

        file_path = self.needs_action / filename
        file_path.write_text(content)

        self.logger.info(f"Created action file {filename}")


# ================= CLI ================= #

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("vault_path")
    parser.add_argument("--session", default=".linkedin_session")
    parser.add_argument("--authenticate", action="store_true")
    parser.add_argument("--post")
    parser.add_argument("--hashtags", nargs="+")
    parser.add_argument("--check", action="store_true")

    args = parser.parse_args()

    watcher = LinkedInWatcher(
        args.vault_path,
        args.session
    )

    if args.authenticate:
        watcher.authenticate()

    elif args.post:
        watcher.post_update(args.post, args.hashtags)

    elif args.check:
        notes = watcher.check_notifications()
        print(f"Found {len(notes)} notifications")

    else:
        watcher.run()


if __name__ == "__main__":
    main()