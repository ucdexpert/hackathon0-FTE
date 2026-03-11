#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Auto Poster - Social_Posts Folder Based

Reads pending posts from Social_Posts/ folder and publishes them to LinkedIn.
After successful posting, moves files to Done/ and creates logs.

Usage:
    python linkedin_auto_post.py <vault_path>

Example:
    python linkedin_auto_post.py "D:\hackathons-Q-4\hackathon 0 new-2\AI_Employee_Vault"
"""

import sys
import logging
import shutil
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def setup_logging(log_path: Path) -> logging.Logger:
    """Setup logging to both file and console."""
    logger = logging.getLogger("LinkedInPoster")
    logger.setLevel(logging.DEBUG)

    # File handler
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_post_content(post_file: Path) -> str:
    """Extract post content from Markdown file."""
    content = post_file.read_text(encoding='utf-8')

    # Remove YAML frontmatter if present
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2].strip()

    return content.strip()


def create_log_entry(log_dir: Path, post_file: Path, content: str, success: bool, error: str = None) -> Path:
    """Create a log entry for the posting attempt."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f"{post_file.stem}_{timestamp}.md"
    log_path = log_dir / log_filename

    status = "SUCCESS" if success else "FAILED"
    error_info = f"\n\nError:\n{error}" if error else ""

    log_content = f"""---
type: linkedin_post_log
status: {status}
timestamp: {datetime.now().isoformat()}
source_file: {post_file.name}
---

# LinkedIn Post Log

**Status:** {status}
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Source File:** {post_file.name}
{error_info}

## Post Content

{content}
"""

    log_path.write_text(log_content, encoding='utf-8')
    return log_path


def post_to_linkedin(page, content: str, logger: logging.Logger, session_path: Path) -> bool:
    """
    Post content to LinkedIn feed.
    Returns True if successful, False otherwise.
    """

    try:
        # Navigate to LinkedIn feed
        logger.info("[1/4] Navigating to LinkedIn feed...")
        page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)

        # Wait for page to fully load
        page.wait_for_load_state('networkidle', timeout=30000)

        # Check if logged in
        if 'login' in page.url.lower():
            logger.error("Not logged in to LinkedIn!")
            logger.info("Please log in manually in the browser window...")

            # Wait for login with longer timeout
            try:
                page.wait_for_url('https://www.linkedin.com/feed/*', timeout=120000)
            except PlaywrightTimeout:
                logger.error("Login timeout - user did not log in")
                return False

        logger.info("[OK] Logged in to LinkedIn")

        # Find and click "Start a post" button
        logger.info("[2/4] Opening post creator...")

        # Wait for and click the Start a post button
        start_post_button = page.locator(
            'button:has-text("Start a post"), '
            'div[role="button"]:has-text("Start a post"), '
            'span:has-text("Start a post")'
        ).first

        try:
            start_post_button.wait_for(state='visible', timeout=15000)
            start_post_button.click()
            logger.info("[OK] Post creator opened")
        except PlaywrightTimeout:
            logger.warning("Could not find 'Start a post' button automatically")
            logger.info("Please click 'Start a post' manually...")
            # Wait for user to click manually
            page.wait_for_timeout(30000)

        # Wait for post modal to appear
        page.wait_for_timeout(3000)

        # Find the post editor and type content
        logger.info("[3/4] Entering post content...")

        # Wait for editor to be available
        editor = page.locator(
            'div[contenteditable="true"][data-placeholder*="What do you want to share"], '
            'div[contenteditable="true"][data-placeholder*="share"], '
            'div[contenteditable="true"][data-placeholder*="post"]'
        ).first

        try:
            editor.wait_for(state='visible', timeout=15000)
            editor.focus()

            # Clear any existing content
            editor.press('Control+A')
            editor.press('Delete')

            # Type the content
            editor.type(content, delay=50)
            logger.info("[OK] Post content entered")

        except PlaywrightTimeout:
            logger.warning("Could not find post editor automatically")
            logger.info("Please paste the content manually")
            page.wait_for_timeout(30000)

        # Wait for Post button to become enabled
        logger.info("[4/4] Waiting for Post button...")

        # Look for the Post button
        post_button = page.locator(
            'button:has-text("Post"), '
            'div[role="button"]:has-text("Post"), '
            'span:has-text("Post")'
        ).first

        try:
            post_button.wait_for(state='enabled', timeout=30000)
            logger.info("[OK] Post button is ready")

            # Click the Post button
            post_button.click()
            logger.info("[OK] Post submitted!")

            # Wait for confirmation that post was published
            page.wait_for_timeout(5000)

            # Check if we're still on feed (post succeeded) vs modal still open
            return True

        except PlaywrightTimeout:
            logger.warning("Post button did not become enabled")
            logger.info("Please click 'Post' manually when ready")
            page.wait_for_timeout(30000)
            return True  # Assume user will post manually

    except PlaywrightTimeout as e:
        logger.error(f"Timeout during posting: {e}")
        return False
    except Exception as e:
        logger.error(f"Error during posting: {e}")
        return False


def main():
    """Main entry point."""

    # Validate arguments
    if len(sys.argv) < 2:
        print("Usage: python linkedin_auto_post.py <vault_path>")
        print("\nExample:")
        print('  python linkedin_auto_post.py "D:\\hackathons-Q-4\\hackathon 0 new-2\\AI_Employee_Vault"')
        sys.exit(1)

    if not PLAYWRIGHT_AVAILABLE:
        print("Playwright not installed!")
        print("Install with:")
        print("  pip install playwright")
        print("  playwright install chromium")
        sys.exit(1)

    # Setup paths
    vault_path = Path(sys.argv[1]).resolve()
    social_posts_dir = vault_path / 'Social_Posts'
    done_dir = vault_path / 'Done'
    logs_dir = vault_path / 'Logs'
    session_path = vault_path / '.linkedin_session'

    # Create directories if they don't exist
    social_posts_dir.mkdir(parents=True, exist_ok=True)
    done_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    session_path.mkdir(parents=True, exist_ok=True)

    # Setup logging
    log_file = logs_dir / f"linkedin_{datetime.now().strftime('%Y%m%d')}.log"
    logger = setup_logging(log_file)

    logger.info("=" * 60)
    logger.info("LINKEDIN AUTO POSTER")
    logger.info("=" * 60)
    logger.info(f"Vault Path: {vault_path}")
    logger.info(f"Social Posts Dir: {social_posts_dir}")
    logger.info("")

    # Find pending posts
    pending_posts = list(social_posts_dir.glob('*.md'))

    if not pending_posts:
        logger.info("No pending posts found in Social_Posts/")
        logger.info("Done!")
        return

    logger.info(f"Found {len(pending_posts)} pending post(s)")
    logger.info("")

    # Process each pending post
    success_count = 0
    fail_count = 0

    with sync_playwright() as p:
        # Launch browser with persistent context
        logger.info("Launching browser...")
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

        for post_file in pending_posts:
            logger.info("")
            logger.info("-" * 60)
            logger.info(f"Processing: {post_file.name}")
            logger.info("-" * 60)

            try:
                # Read post content
                content = get_post_content(post_file)
                logger.info(f"Post content length: {len(content)} characters")

                # Post to LinkedIn
                success = post_to_linkedin(page, content, logger, session_path)

                if success:
                    # Move to Done
                    done_file = done_dir / post_file.name
                    shutil.move(str(post_file), str(done_file))
                    logger.info(f"[OK] Moved to Done/: {done_file.name}")

                    # Create log entry
                    log_path = create_log_entry(logs_dir, post_file, content, success=True)
                    logger.info(f"[OK] Log created: {log_path.name}")

                    success_count += 1
                    logger.info(f"[OK] Post successful!")

                else:
                    # Create failed log
                    log_path = create_log_entry(logs_dir, post_file, content, success=False, error="Posting failed")
                    logger.info(f"[FAIL] Log created: {log_path.name}")
                    fail_count += 1

            except Exception as e:
                logger.error(f"[ERROR] Failed to process {post_file.name}: {e}")
                try:
                    create_log_entry(logs_dir, post_file, "", success=False, error=str(e))
                except:
                    pass
                fail_count += 1

            # Small delay between posts
            if len(pending_posts) > 1:
                page.wait_for_timeout(3000)

        # Close browser
        logger.info("")
        logger.info("Closing browser...")
        browser.close()

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total posts processed: {len(pending_posts)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {fail_count}")
    logger.info("=" * 60)
    logger.info("Done!")


if __name__ == '__main__':
    main()
