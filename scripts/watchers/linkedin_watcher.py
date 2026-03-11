#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Watcher - Gold Tier
Continuously monitors LinkedIn notifications and posts updates.
Follows BaseWatcher pattern from hackathon architecture.

Usage:
    python linkedin_watcher.py /path/to/vault --authenticate
    python linkedin_watcher.py /path/to/vault --post "Hello LinkedIn!" --hashtags ai python
    python linkedin_watcher.py /path/to/vault          # Start continuous watcher
"""

import sys
import time
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Dict

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Missing dependency. Install with:")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)

# ─────────────────────────────────────────────
#  LOGGING SETUP
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)


# ─────────────────────────────────────────────
#  BASE WATCHER  (from hackathon architecture)
# ─────────────────────────────────────────────
class BaseWatcher(ABC):
    """
    Base class for all Watchers.
    Follows the pattern defined in hackathon document Section 2A.
    """

    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.done = self.vault_path / "Done"
        self.logs = self.vault_path / "Logs"
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)

        # Ensure vault directories exist
        for folder in [self.needs_action, self.done, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def check_for_updates(self) -> List[Dict]:
        """
        Check for new items to process.
        Must return a list of dicts describing each new item.
        """
        pass

    @abstractmethod
    def create_action_file(self, item: Dict) -> Path:
        """
        Create a .md file in Needs_Action folder for Claude to process.
        Must return the path to the created file.
        """
        pass

    def log_action(self, action_type: str, details: dict):
        """Write audit log entry (Section 6.3 requirement)."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": "linkedin_watcher",
            **details
        }
        log_file = self.logs / f"{datetime.now().strftime('%Y-%m-%d')}.json"

        entries = []
        if log_file.exists():
            try:
                entries = json.loads(log_file.read_text())
            except Exception:
                entries = []

        entries.append(log_entry)
        log_file.write_text(json.dumps(entries, indent=2))

    def run(self):
        """
        Main continuous loop — the core of the Watcher pattern.
        Runs forever, checking for updates every check_interval seconds.
        Handles errors gracefully so the loop never dies unexpectedly.
        """
        self.logger.info("=" * 55)
        self.logger.info(f"  {self.__class__.__name__} STARTED")
        self.logger.info(f"  Vault        : {self.vault_path}")
        self.logger.info(f"  Needs_Action : {self.needs_action}")
        self.logger.info(f"  Check every  : {self.check_interval}s")
        self.logger.info("=" * 55)

        consecutive_errors = 0
        MAX_CONSECUTIVE_ERRORS = 5

        while True:
            try:
                self.logger.info("Checking for updates...")

                items = self.check_for_updates()

                if items:
                    self.logger.info(f"Found {len(items)} new item(s)")
                    for item in items:
                        file_path = self.create_action_file(item)
                        self.logger.info(f"  → Created: {file_path.name}")
                        self.log_action("action_file_created", {
                            "file": str(file_path.name),
                            "item_type": item.get("type", "unknown")
                        })
                else:
                    self.logger.info("No new items found.")

                # Reset error counter on success
                consecutive_errors = 0

            except KeyboardInterrupt:
                self.logger.info("Watcher stopped by user (Ctrl+C).")
                break

            except Exception as e:
                consecutive_errors += 1
                self.logger.error(f"Error in check loop (attempt {consecutive_errors}): {e}")
                self.log_action("watcher_error", {"error": str(e)})

                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    self.logger.critical(
                        f"Too many consecutive errors ({MAX_CONSECUTIVE_ERRORS}). "
                        "Pausing for 10 minutes before retrying..."
                    )
                    time.sleep(600)
                    consecutive_errors = 0

            self.logger.info(f"Sleeping {self.check_interval}s until next check...\n")
            time.sleep(self.check_interval)


# ─────────────────────────────────────────────
#  LINKEDIN WATCHER  (extends BaseWatcher)
# ─────────────────────────────────────────────
class LinkedInWatcher(BaseWatcher):
    """
    Watches LinkedIn for new notifications matching keywords.
    Posts updates on behalf of the AI Employee.
    Gold Tier — Silver requirement: 2+ watchers + LinkedIn posting.
    """

    LINKEDIN_FEED = "https://www.linkedin.com/feed/"
    LINKEDIN_NOTIFS = "https://www.linkedin.com/notifications/"

    def __init__(
        self,
        vault_path: str,
        session_path: str,
        check_interval: int = 300,
        keywords: List[str] = None
    ):
        super().__init__(vault_path, check_interval)

        self.session_path = Path(session_path)
        self.session_path.mkdir(parents=True, exist_ok=True)

        self.keywords = keywords or ["comment", "message", "connection", "invoice", "urgent"]

        # Track already-processed notifications to avoid duplicates
        self._processed_ids: set = set()

        # Load previously seen IDs from disk so restarts don't re-trigger old items
        self._seen_ids_file = self.vault_path / ".linkedin_seen_ids.json"
        self._load_seen_ids()

    # ── persistence of seen IDs ──────────────────────────────

    def _load_seen_ids(self):
        if self._seen_ids_file.exists():
            try:
                data = json.loads(self._seen_ids_file.read_text())
                self._processed_ids = set(data)
                self.logger.info(f"Loaded {len(self._processed_ids)} previously seen notification IDs.")
            except Exception:
                self._processed_ids = set()

    def _save_seen_ids(self):
        # Keep only last 500 IDs to avoid unbounded growth
        ids_list = list(self._processed_ids)[-500:]
        self._seen_ids_file.write_text(json.dumps(ids_list, indent=2))

    # ── browser context helper ───────────────────────────────

    def _get_browser_context(self, playwright, headless: bool = True):
        return playwright.chromium.launch_persistent_context(
            str(self.session_path),
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
            viewport={"width": 1280, "height": 720},
        )

    # ── session check ─────────────────────────────────────────

    def _is_authenticated(self) -> bool:
        """Return True if session data exists on disk."""
        return self.session_path.exists() and any(self.session_path.iterdir())

    # ── AUTHENTICATE ─────────────────────────────────────────

    def authenticate(self) -> bool:
        """
        Open headed browser so user can log in manually.
        Session is saved to disk for all future runs.
        """
        self.logger.info("Starting LinkedIn authentication (headed browser)...")

        with sync_playwright() as p:
            browser = self._get_browser_context(p, headless=False)
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto("https://www.linkedin.com/login")

            print("\n" + "=" * 50)
            print("  Log in to LinkedIn in the browser window.")
            print("  Session will save automatically.")
            print("  Waiting up to 5 minutes...")
            print("=" * 50 + "\n")

            try:
                page.wait_for_url("https://www.linkedin.com/feed/*", timeout=300_000)
                self.logger.info("Login detected — session saved.")
                time.sleep(2)
                browser.close()
                return True
            except PlaywrightTimeout:
                self.logger.warning("Login timed out.")
                browser.close()
                return False

    # ── CHECK FOR UPDATES (BaseWatcher requirement) ───────────

    def check_for_updates(self) -> List[Dict]:
        """
        Navigate to LinkedIn notifications page and return
        any unseen notifications that match our keywords.
        """
        if not self._is_authenticated():
            self.logger.warning("No session found. Run --authenticate first.")
            return []

        notifications = []

        with sync_playwright() as p:
            browser = self._get_browser_context(p, headless=True)
            page = browser.pages[0] if browser.pages else browser.new_page()

            try:
                self.logger.debug("Navigating to notifications...")
                page.goto(self.LINKEDIN_NOTIFS, wait_until="domcontentloaded", timeout=60_000)
                time.sleep(5)  # Let dynamic content render

                # ── Try multiple selectors (LinkedIn changes DOM often) ──
                NOTIFICATION_SELECTORS = [
                    "[data-test-id='notification-item']",          # Old LinkedIn
                    "li.notification-item",                         # Alternative
                    "div.nt-card-list__item",                       # 2024+ LinkedIn
                    "section.notification",                          # Another variant
                    "article",                                       # Generic fallback
                ]

                items = []
                for selector in NOTIFICATION_SELECTORS:
                    items = page.query_selector_all(selector)
                    if items:
                        self.logger.debug(f"Found {len(items)} items via: {selector}")
                        break

                if not items:
                    self.logger.info("No notification elements found with known selectors.")

                for item in items[:15]:  # Limit to latest 15
                    try:
                        text = item.inner_text(timeout=2_000).strip()
                        if not text:
                            continue

                        notif_id = str(hash(text[:120]))  # Hash of first 120 chars as ID

                        if notif_id in self._processed_ids:
                            continue  # Already processed

                        text_lower = text.lower()
                        matched_keywords = [kw for kw in self.keywords if kw in text_lower]

                        if matched_keywords:
                            notifications.append({
                                "type": "linkedin_notification",
                                "id": notif_id,
                                "text": text,
                                "keywords": matched_keywords,
                                "timestamp": datetime.now().isoformat(),
                            })
                            self._processed_ids.add(notif_id)

                    except Exception:
                        continue

            except Exception as e:
                self.logger.error(f"Error reading notifications: {e}")

            finally:
                browser.close()

        # Persist seen IDs after every check
        self._save_seen_ids()

        return notifications

    # ── CREATE ACTION FILE (BaseWatcher requirement) ──────────

    def create_action_file(self, item: Dict) -> Path:
        """
        Write a .md file to /Needs_Action so Claude Code can process it.
        """
        filename = f"LINKEDIN_NOTIF_{int(time.time())}.md"
        filepath = self.needs_action / filename

        content = f"""---
type: linkedin_notification
received: {item['timestamp']}
keywords: {', '.join(item['keywords'])}
priority: high
status: pending
source: LinkedIn
---

## LinkedIn Notification

{item['text']}

## Keywords Matched

{', '.join(item['keywords'])}

## Suggested Actions

- [ ] Review notification on LinkedIn
- [ ] Reply if it requires a response
- [ ] If it is a business lead — create a follow-up task
- [ ] Archive after processing

---
*Generated by LinkedInWatcher (Gold Tier AI Employee)*
"""
        filepath.write_text(content, encoding="utf-8")
        return filepath

    # ── POST UPDATE ───────────────────────────────────────────

    def post_update(
        self,
        content: str,
        hashtags: List[str] = None,
        screenshot: bool = True,
        dry_run: bool = False
    ) -> Dict:
        """
        Post a LinkedIn update on behalf of the AI Employee.

        Args:
            content   : Post text
            hashtags  : List of hashtag words (without #)
            screenshot: Save proof screenshot to /Done
            dry_run   : If True, log intended action but do NOT post

        Returns:
            Dict with status and optional screenshot path
        """
        if hashtags:
            content += "\n\n" + " ".join(f"#{h}" for h in hashtags)

        # ── DRY RUN (Section 6.2 requirement) ────────────────
        if dry_run:
            self.logger.info(f"[DRY RUN] Would post to LinkedIn:\n{content}")
            self.log_action("linkedin_post_dry_run", {"content_preview": content[:100]})
            return {"status": "dry_run", "content": content}

        result = {"status": "unknown", "content": content}

        if not self._is_authenticated():
            self.logger.warning("No session found. Run --authenticate first.")
            result["status"] = "error"
            result["error"] = "Not authenticated"
            return result

        with sync_playwright() as p:
            browser = self._get_browser_context(p, headless=True)
            page = browser.pages[0] if browser.pages else browser.new_page()

            try:
                # ── Navigate to feed ─────────────────────────
                self.logger.info("Navigating to LinkedIn feed...")
                page.goto(self.LINKEDIN_FEED, wait_until="domcontentloaded", timeout=60_000)
                time.sleep(8)

                # ── Open post creator ─────────────────────────
                self.logger.info("Opening post creator...")
                opened = self._open_post_creator(page)
                if not opened:
                    raise RuntimeError("Could not open post creator.")

                time.sleep(4)

                # ── Enter content ─────────────────────────────
                self.logger.info("Entering post content...")
                entered = self._enter_content(page, content)
                if not entered:
                    raise RuntimeError("Could not enter content in editor.")

                time.sleep(2)

                # ── Submit post ───────────────────────────────
                self.logger.info("Submitting post...")
                self._submit_post(page)
                time.sleep(6)

                result["status"] = "posted"
                result["timestamp"] = datetime.now().isoformat()
                self.logger.info("Post submitted successfully.")

                # ── Screenshot proof ──────────────────────────
                if screenshot:
                    shot_path = self.done / f"linkedin_post_{int(time.time())}.png"
                    page.screenshot(path=str(shot_path))
                    result["screenshot"] = str(shot_path)
                    self.logger.info(f"Screenshot saved: {shot_path.name}")

                self.log_action("linkedin_post", {
                    "status": "posted",
                    "content_preview": content[:80]
                })

            except Exception as e:
                self.logger.error(f"Post failed: {e}")
                result["status"] = "error"
                result["error"] = str(e)
                self.log_action("linkedin_post_error", {"error": str(e)})

            finally:
                browser.close()

        return result

    # ── private posting helpers ───────────────────────────────

    def _open_post_creator(self, page) -> bool:
        """Click 'Start a post' button. Returns True on success."""

        # Method 1: JavaScript (most reliable)
        opened = page.evaluate("""() => {
            for (let btn of document.querySelectorAll('button')) {
                if (btn.textContent.includes('Start a post') && btn.offsetParent !== null) {
                    btn.click();
                    return true;
                }
            }
            return false;
        }""")
        if opened:
            return True

        # Method 2: Playwright selectors
        for selector in [
            'button:has-text("Start a post")',
            '[aria-label*="Start a post"]',
            'div.share-box-feed-entry__trigger',
        ]:
            try:
                page.locator(selector).first.click(timeout=5_000)
                return True
            except Exception:
                continue

        return False

    def _enter_content(self, page, content: str) -> bool:
        """Type content into the post editor. Returns True on success."""

        # Wait for any editor to appear
        time.sleep(3)

        for selector in [
            'div[contenteditable="true"][role="textbox"]',
            'div[contenteditable="true"]',
            '.ql-editor',
        ]:
            try:
                editor = page.locator(selector).first
                editor.wait_for(state="visible", timeout=5_000)
                editor.click()
                time.sleep(0.5)
                page.keyboard.press("Control+a")
                time.sleep(0.3)
                page.keyboard.press("Backspace")
                time.sleep(0.3)
                page.keyboard.type(content, delay=40)
                return True
            except Exception:
                continue

        # Fallback: JavaScript execCommand
        result = page.evaluate("""(text) => {
            for (let el of document.querySelectorAll('div[contenteditable="true"]')) {
                if (el.offsetParent !== null) {
                    el.focus();
                    document.execCommand('insertText', false, text);
                    return true;
                }
            }
            return false;
        }""", content)

        return bool(result)

    def _submit_post(self, page):
        """Click the Post button or fall back to Control+Enter."""

        for selector in [
            'button:has-text("Post")',
            'button:has-text("Share")',
            'button[aria-label*="Post"]',
        ]:
            try:
                btn = page.locator(selector).first
                if btn.is_enabled(timeout=5_000):
                    btn.click()
                    return
            except Exception:
                continue

        # JS fallback
        clicked = page.evaluate("""() => {
            for (let btn of document.querySelectorAll('button')) {
                if ((btn.textContent.trim() === 'Post' || btn.textContent.trim() === 'Share')
                        && btn.offsetParent !== null) {
                    btn.click();
                    return true;
                }
            }
            return false;
        }""")

        if not clicked:
            self.logger.info("Using Control+Enter as final fallback...")
            page.keyboard.press("Control+Enter")


# ─────────────────────────────────────────────
#  CLI ENTRY POINT
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="LinkedIn Watcher — Gold Tier AI Employee"
    )
    parser.add_argument("vault_path", help="Path to Obsidian vault")
    parser.add_argument("--session", "-s",
                        help="Path to browser session folder",
                        default=None)
    parser.add_argument("--interval", "-i", type=int, default=300,
                        help="Check interval in seconds (default: 300)")
    parser.add_argument("--keywords", "-k", nargs="+",
                        help="Keywords to monitor in notifications")
    parser.add_argument("--authenticate", "-a", action="store_true",
                        help="Run LinkedIn login flow (headed browser)")
    parser.add_argument("--post", "-p",
                        help="Post content to LinkedIn")
    parser.add_argument("--hashtags", "-H", nargs="+",
                        help="Hashtags to append to post (without #)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Log intended action without actually posting")
    parser.add_argument("--check", "-c", action="store_true",
                        help="Check notifications once and exit")

    args = parser.parse_args()

    vault_path = Path(args.vault_path)
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    session_path = args.session or str(vault_path / ".linkedin_session")

    watcher = LinkedInWatcher(
        vault_path=str(vault_path),
        session_path=session_path,
        check_interval=args.interval,
        keywords=args.keywords,
    )

    # ── Route to correct action ──────────────────────────────
    if args.authenticate:
        print("\nOpening browser for LinkedIn login...")
        success = watcher.authenticate()
        if success:
            print("\n✓ Authentication successful! Session saved.")
            print("  You can now run the watcher without --authenticate.")
        else:
            print("\n✗ Authentication failed. Try again.")
            sys.exit(1)

    elif args.post:
        print(f"\nPosting to LinkedIn: {args.post[:60]}...")
        result = watcher.post_update(
            content=args.post,
            hashtags=args.hashtags,
            dry_run=args.dry_run
        )
        print(f"\nResult : {result['status']}")
        if result.get("screenshot"):
            print(f"Proof  : {result['screenshot']}")

    elif args.check:
        print("\nChecking LinkedIn notifications once...")
        items = watcher.check_for_updates()
        if items:
            print(f"\nFound {len(items)} new notification(s):")
            for item in items:
                print(f"  [{', '.join(item['keywords'])}] {item['text'][:80]}...")
                path = watcher.create_action_file(item)
                print(f"  → Saved: {path.name}")
        else:
            print("No new notifications matching keywords.")

    else:
        # ── CONTINUOUS WATCHER LOOP ──────────────────────────
        print("\nStarting continuous LinkedIn Watcher...")
        print("Press Ctrl+C to stop.\n")
        watcher.run()


if __name__ == "__main__":
    main()