#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail Watcher - Monitors Gmail for new important emails.

Uses your existing credentials.json for Gmail API authentication.
Creates action files in /Needs_Action folder for Qwen Code to process.

Usage:
    python gmail_watcher.py <vault_path> [--interval SECONDS] [--keywords KEYWORDS]

Examples:
    python gmail_watcher.py .
    python gmail_watcher.py . --interval 60 --keywords "urgent,invoice,payment"
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from base_watcher import BaseWatcher, create_frontmatter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False
    print("\nGoogle libraries not installed.")
    print("Install with: pip install google-auth google-auth-oauthlib google-api-python-client\n")


class GmailWatcher(BaseWatcher):
    """Watcher that monitors Gmail for new important emails."""
    
    # Gmail API scopes
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    # Default keywords to filter important emails
    DEFAULT_KEYWORDS = ['urgent', 'asap', 'invoice', 'payment', 'help', 'important']
    
    def __init__(self, vault_path: str, credentials_path: str = None,
                 check_interval: int = 120, keywords: List[str] = None):
        """
        Initialize the Gmail watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            credentials_path: Path to credentials.json (default: ./credentials.json)
            check_interval: Seconds between checks (default: 120)
            keywords: List of keywords to filter important emails
        """
        super().__init__(vault_path, check_interval)
        
        # Use credentials.json from vault root or current directory
        self.credentials_path = Path(credentials_path) if credentials_path else Path('credentials.json')
        self.token_path = Path('token.json')  # OAuth token (auto-generated)
        self.keywords = keywords or self.DEFAULT_KEYWORDS
        self.processed_ids = set()
        self.service = None
        
        # Load previously processed email IDs
        self._load_processed_ids()
        
        self.logger.info(f'Credentials file: {self.credentials_path.absolute()}')
        self.logger.info(f'Token file: {self.token_path.absolute()}')
        self.logger.info(f'Keywords to filter: {self.keywords}')
        self.logger.info(f'Check interval: {check_interval}s')
    
    def _load_processed_ids(self):
        """Load previously processed email IDs from cache file."""
        cache_file = self.vault_path / '.gmail_cache.json'
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                self.processed_ids = set(data.get('processed_ids', []))
                self.logger.info(f'Loaded {len(self.processed_ids)} processed email IDs from cache')
            except Exception as e:
                self.logger.warning(f'Could not load cache: {e}')
    
    def _save_processed_ids(self):
        """Save processed email IDs to cache file."""
        cache_file = self.vault_path / '.gmail_cache.json'
        # Keep only last 1000 IDs to prevent unbounded growth
        ids_list = list(self.processed_ids)[-1000:]
        cache_file.write_text(json.dumps({'processed_ids': ids_list}, indent=2))
    
    def _authenticate(self) -> bool:
        """
        Authenticate with Gmail API using credentials.json.
        
        Returns:
            True if authentication successful, False otherwise
        """
        if not GOOGLE_LIBS_AVAILABLE:
            self.logger.error('Google libraries not installed.')
            self.logger.error('Install with: pip install google-auth google-auth-oauthlib google-api-python-client')
            return False
        
        # Check if credentials.json exists
        if not self.credentials_path.exists():
            self.logger.error(f'Credentials file not found: {self.credentials_path.absolute()}')
            self.logger.error('Please ensure credentials.json exists in the vault root directory.')
            return False
        
        try:
            creds = None
            
            # Load token from previous authentication
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
                self.logger.info('Loaded existing OAuth token')
            
            # Refresh or re-authenticate if no valid credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    self.logger.info('Refreshing expired token...')
                    creds.refresh(Request())
                else:
                    self.logger.info('Starting new OAuth flow...')
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    creds = flow.run_local_server(port=8080)
                
                # Save credentials for next run
                self.token_path.write_text(creds.to_json())
                self.logger.info(f'OAuth token saved to: {self.token_path.absolute()}')
            
            # Build Gmail API service
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info('Successfully authenticated with Gmail API')
            return True
            
        except Exception as e:
            self.logger.error(f'Authentication failed: {e}')
            return False
    
    def _build_query(self) -> str:
        """Build Gmail query string for filtering emails."""
        # Base query: unread messages
        query_parts = ['is:unread']
        
        # Add keyword search
        if self.keywords:
            keyword_query = ' OR '.join(self.keywords)
            query_parts.append(f'({keyword_query})')
        
        return ' '.join(query_parts)
    
    def check_for_updates(self) -> List[dict]:
        """
        Check for new emails in Gmail.
        
        Returns:
            List of new email message dicts
        """
        if not self.service:
            if not self._authenticate():
                return []
        
        try:
            query = self._build_query()
            self.logger.debug(f'Gmail query: {query}')
            
            # Fetch messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            
            # Filter out already processed
            new_messages = [m for m in messages if m['id'] not in self.processed_ids]
            
            if new_messages:
                self.logger.info(f'Found {len(new_messages)} new emails')
            
            return new_messages
            
        except HttpError as e:
            self.logger.error(f'Gmail API error: {e}')
            if e.resp.status == 401:
                # Token expired, try to re-authenticate
                self.service = None
                self._authenticate()
            return []
        except Exception as e:
            self.logger.error(f'Error checking Gmail: {e}')
            return []
    
    def _get_email_details(self, message_id: str) -> dict:
        """Get full email details."""
        message = self.service.users().messages().get(
            userId='me',
            id=message_id,
            format='metadata',
            metadataHeaders=['From', 'To', 'Subject', 'Date']
        ).execute()
        
        # Extract headers
        headers = message.get('payload', {}).get('headers', [])
        email_data = {'id': message_id}
        
        for header in headers:
            name = header['name'].lower()
            value = header['value']
            if name == 'from':
                email_data['from'] = value
            elif name == 'to':
                email_data['to'] = value
            elif name == 'subject':
                email_data['subject'] = value
            elif name == 'date':
                email_data['date'] = value
        
        # Get snippet
        email_data['snippet'] = message.get('snippet', '')
        
        return email_data
    
    def create_action_file(self, message: dict) -> Path:
        """
        Create a .md action file in Needs_Action folder.
        
        Args:
            message: Email message dict with 'id' key
            
        Returns:
            Path to the created file
        """
        # Get full email details
        email_data = self._get_email_details(message['id'])
        
        # Parse sender email
        from_email = email_data.get('from', 'Unknown')
        
        # Create content
        content = f"""{create_frontmatter(
            type='email',
            from_email=from_email,
            subject=email_data.get('subject', 'No Subject'),
            received=datetime.now().isoformat(),
            priority='high',
            status='pending',
            message_id=message['id']
        )}

# Email Received

**From:** {from_email}

**Subject:** {email_data.get('subject', 'No Subject')}

**Date:** {email_data.get('date', 'Unknown')}

---

## Preview

{email_data.get('snippet', 'No preview available')}

---

## Suggested Actions

- [ ] Read full email in Gmail
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing

---

*Created by Gmail Watcher*
"""
        # Write action file
        filepath = self.needs_action / f"EMAIL_{message['id']}.md"
        filepath.write_text(content, encoding='utf-8')
        
        # Mark as processed
        self.processed_ids.add(message['id'])
        self._save_processed_ids()
        
        return filepath
    
    def run(self):
        """Main run loop."""
        self.logger.info('=' * 60)
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.logger.info('=' * 60)
        self.logger.info(f'Vault path: {self.vault_path.absolute()}')
        self.logger.info(f'Check interval: {self.check_interval}s')
        
        # Check for Google libraries
        if not GOOGLE_LIBS_AVAILABLE:
            self.logger.error('Google libraries not installed.')
            self.logger.error('Install with: pip install google-auth google-auth-oauthlib google-api-python-client')
            return
        
        # Check if credentials.json exists
        if not self.credentials_path.exists():
            self.logger.error(f'Credentials file not found: {self.credentials_path.absolute()}')
            self.logger.error('Please run: python gmail_watcher.py . --authenticate')
            return
        
        # Try initial authentication
        if not self._authenticate():
            self.logger.error('Failed to authenticate. Run with --authenticate flag first.')
            return
        
        self.logger.info('=' * 60)
        self.logger.info('Gmail Watcher is now running...')
        self.logger.info('Press Ctrl+C to stop')
        self.logger.info('=' * 60)
        
        try:
            while True:
                try:
                    items = self.check_for_updates()
                    for item in items:
                        filepath = self.create_action_file(item)
                        self.logger.info(f'Created action file: {filepath.name}')
                except Exception as e:
                    self.logger.error(f'Error processing updates: {e}')
                
                import time
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info(f'\n{self.__class__.__name__} stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}')
            raise


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Gmail Watcher - Monitor Gmail for important emails',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python gmail_watcher.py .
  python gmail_watcher.py . --interval 60 --keywords "urgent,invoice,payment"
  python gmail_watcher.py . --authenticate
        """
    )
    parser.add_argument('vault_path', nargs='?', default='.', help='Path to Obsidian vault')
    parser.add_argument('--interval', '-i', type=int, default=120, help='Check interval in seconds (default: 120)')
    parser.add_argument('--keywords', '-k', type=str, default='', help='Comma-separated keywords to filter')
    parser.add_argument('--credentials', '-c', type=str, default='credentials.json', help='Path to credentials.json')
    parser.add_argument('--authenticate', '-a', action='store_true', help='Run authentication only')
    
    args = parser.parse_args()
    
    # Parse keywords
    keywords = [k.strip() for k in args.keywords.split(',')] if args.keywords else None
    
    if args.authenticate:
        # Just authenticate and exit
        if not GOOGLE_LIBS_AVAILABLE:
            print('\nGoogle libraries not installed.')
            print('Install with: pip install google-auth google-auth-oauthlib google-api-python-client\n')
            sys.exit(1)
        
        credentials_path = Path(args.credentials)
        
        if not credentials_path.exists():
            print(f'\nCredentials file not found: {credentials_path.absolute()}')
            print('Please ensure credentials.json exists in the vault root directory.\n')
            sys.exit(1)
        
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        
        SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        
        print('\n' + '=' * 60)
        print('Gmail OAuth Authentication')
        print('=' * 60)
        print(f'\nCredentials: {credentials_path.absolute()}')
        print('\nOpening browser for authentication...')
        print('Please log in to your Google account and grant permissions.\n')
        
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        creds = flow.run_local_server(port=8080)
        
        token_path = Path('token.json')
        token_path.write_text(creds.to_json())
        
        print('\n' + '=' * 60)
        print('Authentication successful!')
        print('=' * 60)
        print(f'\nToken saved to: {token_path.absolute()}')
        print('\nYou can now run the Gmail Watcher:')
        print('  python gmail_watcher.py .\n')
        sys.exit(0)
    
    watcher = GmailWatcher(
        vault_path=args.vault_path,
        credentials_path=args.credentials,
        check_interval=args.interval,
        keywords=keywords
    )
    watcher.run()


if __name__ == "__main__":
    main()
