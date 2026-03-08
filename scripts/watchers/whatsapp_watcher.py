#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WhatsApp Watcher - Monitors WhatsApp Web for urgent messages.

Uses Playwright to automate WhatsApp Web and detect messages with keywords.
Creates action files in /Needs_Action folder for Qwen Code to process.

WARNING: Be aware of WhatsApp's terms of service when using automation.

Usage:
    python whatsapp_watcher.py <vault_path> [--interval SECONDS] [--keywords KEYWORDS]
    
Examples:
    python whatsapp_watcher.py .
    python whatsapp_watcher.py . --interval 30 --keywords "urgent,invoice,payment"
"""

import sys
import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from base_watcher import BaseWatcher, create_frontmatter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not installed. Run: pip install playwright && playwright install")


class WhatsAppWatcher(BaseWatcher):
    """Watcher that monitors WhatsApp Web for urgent messages."""
    
    # Default keywords to filter important messages
    DEFAULT_KEYWORDS = ['urgent', 'asap', 'invoice', 'payment', 'help', 'emergency']
    
    # WhatsApp Web URL
    WHATSAPP_WEB_URL = 'https://web.whatsapp.com'
    
    def __init__(self, vault_path: str, session_path: str = None,
                 check_interval: int = 30, keywords: List[str] = None,
                 headless: bool = False):
        """
        Initialize the WhatsApp watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            session_path: Path to store browser session data
            check_interval: Seconds between checks (default: 30)
            keywords: List of keywords to filter urgent messages
            headless: Run browser in headless mode (default: False)
        """
        super().__init__(vault_path, check_interval)
        
        # Session path for persistent login
        self.session_path = Path(session_path) if session_path else self.vault_path / '.whatsapp_session'
        self.session_path.mkdir(parents=True, exist_ok=True)
        
        self.keywords = [k.lower().strip() for k in (keywords or self.DEFAULT_KEYWORDS)]
        self.headless = headless
        self.processed_chats = set()
        
        # Load previously processed chats
        self._load_processed_chats()
        
        self.logger.info(f'Keywords to filter: {self.keywords}')
        self.logger.info(f'Session path: {self.session_path}')
    
    def _load_processed_chats(self):
        """Load previously processed chat IDs from cache file."""
        cache_file = self.vault_path / '.whatsapp_cache.json'
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                self.processed_chats = set(data.get('processed_chats', []))
                self.logger.info(f'Loaded {len(self.processed_chats)} processed chat IDs from cache')
            except Exception as e:
                self.logger.warning(f'Could not load cache: {e}')
    
    def _save_processed_chats(self):
        """Save processed chat IDs to cache file."""
        cache_file = self.vault_path / '.whatsapp_cache.json'
        # Keep only last 500 chats to prevent unbounded growth
        chats_list = list(self.processed_chats)[-500:]
        cache_file.write_text(json.dumps({'processed_chats': chats_list}, indent=2))
    
    def _check_for_keyword_match(self, text: str) -> List[str]:
        """Check if text contains any keywords."""
        text_lower = text.lower()
        matched = [kw for kw in self.keywords if kw in text_lower]
        return matched
    
    def check_for_updates(self) -> List[Dict]:
        """
        Check for new urgent messages on WhatsApp Web.
        
        Returns:
            List of message dicts with chat info and text
        """
        if not PLAYWRIGHT_AVAILABLE:
            self.logger.error('Playwright not installed')
            return []
        
        messages = []
        
        try:
            with sync_playwright() as p:
                # Launch browser with persistent context
                browser = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox'
                    ]
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                # Navigate to WhatsApp Web
                self.logger.info('Navigating to WhatsApp Web...')
                page.goto(self.WHATSAPP_WEB_URL, wait_until='domcontentloaded', timeout=60000)
                
                # Wait for chat list to load (or QR code on first run)
                try:
                    page.wait_for_selector('[data-testid="chat-list"]', timeout=30000)
                except PlaywrightTimeout:
                    self.logger.warning('WhatsApp Web not loaded. Please scan QR code if first run.')
                    # Wait additional time for QR scan
                    try:
                        page.wait_for_selector('[data-testid="chat-list"]', timeout=60000)
                    except PlaywrightTimeout:
                        self.logger.error('WhatsApp Web failed to load')
                        browser.close()
                        return []
                
                self.logger.info('WhatsApp Web loaded successfully')
                
                # Small delay for content to render
                time.sleep(2)
                
                # Find unread chats with keywords
                try:
                    # Get all chat elements
                    chat_elements = page.query_selector_all('[role="row"]')
                    
                    for chat in chat_elements:
                        try:
                            # Get chat name
                            name_elem = chat.query_selector('[dir="auto"]')
                            chat_name = name_elem.inner_text() if name_elem else 'Unknown'
                            
                            # Get message preview
                            msg_elem = chat.query_selector('span[dir="auto"]')
                            if not msg_elem:
                                continue
                                
                            msg_text = msg_elem.inner_text()
                            
                            # Check for keywords
                            matched_keywords = self._check_for_keyword_match(msg_text)
                            
                            if matched_keywords:
                                # Get chat identifier
                                chat_id = f"{chat_name}_{int(time.time())}"
                                
                                # Skip if already processed recently
                                if chat_id not in self.processed_chats:
                                    messages.append({
                                        'chat_id': chat_id,
                                        'chat_name': chat_name,
                                        'text': msg_text,
                                        'keywords': matched_keywords,
                                        'timestamp': datetime.now()
                                    })
                                    self.processed_chats.add(chat_id)
                                    
                        except Exception as e:
                            self.logger.debug(f'Error processing chat: {e}')
                            continue
                
                except Exception as e:
                    self.logger.error(f'Error scanning chats: {e}')
                
                browser.close()
                
        except Exception as e:
            self.logger.error(f'WhatsApp automation error: {e}')
        
        if messages:
            self._save_processed_chats()
            self.logger.info(f'Found {len(messages)} urgent messages')
        
        return messages
    
    def create_action_file(self, message: Dict) -> Path:
        """
        Create a .md action file in Needs_Action folder.
        
        Args:
            message: Message dict with chat info
            
        Returns:
            Path to the created file
        """
        content = f"""{create_frontmatter(
            type='whatsapp_message',
            chat_name=message['chat_name'],
            received=message['timestamp'].isoformat(),
            priority='high',
            status='pending',
            keywords=','.join(message['keywords'])
        )}

# WhatsApp Message

**From:** {message['chat_name']}

**Received:** {message['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

---

## Message Content

{message['text']}

---

## Detected Keywords

{chr(10).join(f'- {kw}' for kw in message['keywords'])}

---

## Suggested Actions

- [ ] Reply on WhatsApp
- [ ] Take required action
- [ ] Mark as done after response

---

*Created by WhatsApp Watcher*
"""
        # Create filename from chat name and timestamp
        safe_name = "".join(c if c.isalnum() else "_" for c in message['chat_name'])[:30]
        filepath = self.needs_action / f"WHATSAPP_{safe_name}_{message['timestamp'].strftime('%Y%m%d%H%M%S')}.md"
        filepath.write_text(content, encoding='utf-8')
        
        return filepath
    
    def run(self):
        """Main run loop."""
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Check interval: {self.check_interval}s')
        
        # Check for Playwright
        if not PLAYWRIGHT_AVAILABLE:
            self.logger.error('Playwright not installed.')
            self.logger.error('Install with: pip install playwright && playwright install')
            return
        
        try:
            while True:
                try:
                    items = self.check_for_updates()
                    for item in items:
                        filepath = self.create_action_file(item)
                        self.logger.info(f'Created action file: {filepath.name}')
                except Exception as e:
                    self.logger.error(f'Error processing updates: {e}')
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info(f'{self.__class__.__name__} stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}')
            raise


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='WhatsApp Watcher - Monitor WhatsApp Web for urgent messages')
    parser.add_argument('vault_path', nargs='?', default='.', help='Path to Obsidian vault')
    parser.add_argument('--interval', '-i', type=int, default=30, help='Check interval in seconds')
    parser.add_argument('--keywords', '-k', type=str, default='', help='Comma-separated keywords to filter')
    parser.add_argument('--session-path', '-s', type=str, default=None, help='Path to store browser session')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    
    args = parser.parse_args()
    
    # Parse keywords
    keywords = [k.strip() for k in args.keywords.split(',')] if args.keywords else None
    
    if not PLAYWRIGHT_AVAILABLE:
        print('Playwright not installed.')
        print('Install with: pip install playwright && playwright install')
        sys.exit(1)
    
    watcher = WhatsAppWatcher(
        vault_path=args.vault_path,
        session_path=args.session_path,
        check_interval=args.interval,
        keywords=keywords,
        headless=args.headless
    )
    watcher.run()


if __name__ == "__main__":
    main()
