#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Facebook Watcher - Monitors Facebook using Graph API.

Uses Facebook Graph API to monitor:
- Page notifications
- Page messages
- Post comments and engagement
- Page insights

Creates action files in /Needs_Action folder for processing.

Usage:
    python facebook_watcher.py <vault_path> [--interval SECONDS] [--keywords KEYWORDS]

Examples:
    python facebook_watcher.py .
    python facebook_watcher.py . --interval 300 --keywords "urgent,message,inquiry"
"""

import sys
import json
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from base_watcher import BaseWatcher, create_frontmatter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class FacebookWatcher(BaseWatcher):
    """Watcher that monitors Facebook using Graph API."""

    # Default keywords to filter important notifications
    DEFAULT_KEYWORDS = ['urgent', 'message', 'inquiry', 'question', 'order', 'buy', 'price', 'interested']

    def __init__(self, vault_path: str,
                 page_access_token: str = None,
                 page_id: str = None,
                 check_interval: int = 300,
                 keywords: List[str] = None):
        """
        Initialize the Facebook watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            page_access_token: Facebook Page Access Token
            page_id: Facebook Page ID
            check_interval: Seconds between checks (default: 300)
            keywords: List of keywords to filter important notifications
        """
        super().__init__(vault_path, check_interval)

        # Load configuration from .env or parameters
        from dotenv import load_dotenv
        load_dotenv()
        import os

        self.page_access_token = page_access_token or os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
        self.page_id = page_id or os.getenv('FACEBOOK_PAGE_ID')
        self.keywords = keywords or self.DEFAULT_KEYWORDS
        self.processed_ids = set()
        self.graph_api_version = 'v18.0'
        self.base_url = f'https://graph.facebook.com/{self.graph_api_version}'

        self.logger = logging.getLogger(self.__class__.__name__)

        # Load previously processed IDs
        self._load_processed_ids()

        self.logger.info(f'Page ID: {self.page_id or "Not configured"}')
        self.logger.info(f'Keywords to filter: {self.keywords}')
        self.logger.info(f'Check interval: {check_interval}s')
        self.logger.info(f'Graph API Version: {self.graph_api_version}')

    def _load_processed_ids(self):
        """Load previously processed notification IDs from cache file."""
        cache_file = self.vault_path / '.facebook_cache.json'
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                self.processed_ids = set(data.get('processed_ids', []))
                self.logger.info(f'Loaded {len(self.processed_ids)} processed IDs from cache')
            except Exception as e:
                self.logger.warning(f'Could not load cache: {e}')

    def _save_processed_ids(self):
        """Save processed notification IDs to cache file."""
        cache_file = self.vault_path / '.facebook_cache.json'
        # Keep only last 500 IDs to prevent unbounded growth
        ids_list = list(self.processed_ids)[-500:]
        cache_file.write_text(json.dumps({'processed_ids': ids_list}, indent=2))

    def _make_graph_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request to Facebook Graph API."""
        if not self.page_access_token:
            self.logger.error('Page Access Token not configured')
            return {}

        url = f'{self.base_url}/{endpoint}'
        default_params = {'access_token': self.page_access_token}

        if params:
            default_params.update(params)

        try:
            response = requests.get(url, params=default_params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f'Graph API request failed: {e}')
            return {}

    def check_for_updates(self) -> List[Dict]:
        """
        Check Facebook for new notifications, messages, and engagement.

        Returns:
            List of new notification dicts
        """
        if not self.page_access_token or not self.page_id:
            self.logger.warning('Facebook API not configured. Set FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID')
            return []

        notifications = []

        # Get recent messages
        try:
            messages = self._get_recent_messages()
            notifications.extend(messages)
        except Exception as e:
            self.logger.error(f'Error getting messages: {e}')

        # Get recent comments
        try:
            comments = self._get_recent_comments()
            notifications.extend(comments)
        except Exception as e:
            self.logger.error(f'Error getting comments: {e}')

        # Get recent posts engagement
        try:
            engagements = self._get_post_engagements()
            notifications.extend(engagements)
        except Exception as e:
            self.logger.error(f'Error getting engagements: {e}')

        # Filter for keyword matches
        important = []
        for notif in notifications:
            if self._matches_keywords(notif):
                important.append(notif)

        # Filter out already processed
        new_notifications = [n for n in important if n.get('id') not in self.processed_ids]

        if new_notifications:
            self.logger.info(f'Found {len(new_notifications)} new important notifications')

        return new_notifications

    def _get_recent_messages(self) -> List[Dict]:
        """Get recent messages from Page Inbox."""
        messages = []

        # Get conversations
        conversations = self._make_graph_request(
            f'{self.page_id}/conversations',
            {
                'fields': 'messages{from,message,created_time,id}',
                'limit': 10
            }
        )

        if 'data' in conversations:
            for conv in conversations['data']:
                if 'messages' in conv and 'data' in conv['messages']:
                    for msg in conv['messages']['data']:
                        message_text = msg.get('message', '')
                        from_name = msg.get('from', {}).get('name', 'Unknown')

                        messages.append({
                            'id': f"fb_msg_{msg.get('id', '')}",
                            'type': 'message',
                            'from': from_name,
                            'text': message_text,
                            'timestamp': msg.get('created_time', datetime.now().isoformat()),
                            'source': 'facebook_messenger'
                        })

        return messages

    def _get_recent_comments(self) -> List[Dict]:
        """Get recent comments on Page posts."""
        comments = []

        # Get page posts
        posts = self._make_graph_request(
            f'{self.page_id}/posts',
            {'limit': 5}
        )

        if 'data' in posts:
            for post in posts['data']:
                post_id = post.get('id', '')

                # Get comments for each post
                comments_data = self._make_graph_request(
                    f'{post_id}/comments',
                    {
                        'fields': 'from,message,created_time,id',
                        'limit': 10
                    }
                )

                if 'data' in comments_data:
                    for comment in comments_data['data']:
                        comment_text = comment.get('message', '')
                        from_name = comment.get('from', {}).get('name', 'Unknown')

                        comments.append({
                            'id': f"fb_comment_{comment.get('id', '')}",
                            'type': 'comment',
                            'from': from_name,
                            'text': comment_text,
                            'post_id': post_id,
                            'timestamp': comment.get('created_time', datetime.now().isoformat()),
                            'source': 'facebook_comments'
                        })

        return comments

    def _get_post_engagements(self) -> List[Dict]:
        """Get recent post engagements (likes, shares)."""
        engagements = []

        # Get page posts with insights
        posts = self._make_graph_request(
            f'{self.page_id}/posts',
            {
                'fields': 'id,message,created_time,likes.summary(true),shares',
                'limit': 5
            }
        )

        if 'data' in posts:
            for post in posts['data']:
                post_id = post.get('id', '')
                likes_count = post.get('likes', {}).get('summary', {}).get('total_count', 0)
                shares_count = post.get('shares', {}).get('count', 0)

                # Create engagement notification
                if likes_count > 10 or shares_count > 5:
                    engagements.append({
                        'id': f"fb_engagement_{post_id}",
                        'type': 'engagement',
                        'text': f'Post received {likes_count} likes and {shares_count} shares',
                        'post_id': post_id,
                        'timestamp': post.get('created_time', datetime.now().isoformat()),
                        'source': 'facebook_engagement',
                        'metrics': {
                            'likes': likes_count,
                            'shares': shares_count
                        }
                    })

        return engagements

    def _matches_keywords(self, notification: Dict) -> bool:
        """Check if notification matches keywords."""
        text = notification.get('text', '').lower()
        return any(keyword in text for keyword in self.keywords)

    def create_action_file(self, notification: Dict) -> Path:
        """
        Create a .md action file in Needs_Action folder.

        Args:
            notification: Notification dict

        Returns:
            Path to the created file
        """
        notification_type = notification.get('type', 'notification')
        priority = 'high' if notification_type == 'message' else 'normal'

        # Create content
        content = f"""{create_frontmatter(
            type=f'facebook_{notification_type}',
            from_source='Facebook',
            from_name=notification.get('from', 'Unknown'),
            subject=notification.get('text', 'No content')[:100],
            received=datetime.now().isoformat(),
            priority=priority,
            status='pending',
            notification_id=notification.get('id')
        )}

# Facebook {notification_type.title()}

**Source:** Facebook {notification.get('source', 'Unknown').replace('_', ' ').title()}

**From:** {notification.get('from', 'Unknown')}

**Received:** {notification.get('timestamp', 'Unknown')}

**Type:** {notification_type}

---

## Content

{notification.get('text', 'No content')}

---

## Additional Information

{self._format_additional_info(notification)}

---

## Suggested Actions

{self._get_suggested_actions(notification_type)}

---

*Created by Facebook Watcher (Graph API)*
"""
        # Write action file
        filepath = self.needs_action / f"FACEBOOK_{notification['id'][:12]}.md"
        filepath.write_text(content, encoding='utf-8')

        # Mark as processed
        self.processed_ids.add(notification['id'])
        self._save_processed_ids()

        return filepath

    def _format_additional_info(self, notification: Dict) -> str:
        """Format additional information for the action file."""
        lines = []

        if 'post_id' in notification:
            lines.append(f"- **Post ID:** {notification['post_id']}")

        if 'metrics' in notification:
            metrics = notification['metrics']
            lines.append(f"- **Likes:** {metrics.get('likes', 0)}")
            lines.append(f"- **Shares:** {metrics.get('shares', 0)}")

        return '\n'.join(lines) if lines else '*No additional information*'

    def _get_suggested_actions(self, notification_type: str) -> str:
        """Get suggested actions based on notification type."""
        actions = {
            'message': [
                '- [ ] Read full message',
                '- [ ] Respond to customer inquiry',
                '- [ ] Mark as processed'
            ],
            'comment': [
                '- [ ] Review comment',
                '- [ ] Respond if needed',
                '- [ ] Mark as processed'
            ],
            'engagement': [
                '- [ ] Review post performance',
                '- [ ] Consider boosting post',
                '- [ ] Mark as processed'
            ],
            'notification': [
                '- [ ] Review notification',
                '- [ ] Take action if needed',
                '- [ ] Mark as processed'
            ]
        }
        return '\n'.join(actions.get(notification_type, actions['notification']))

    def run(self):
        """Main run loop."""
        self.logger.info('=' * 60)
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.logger.info('=' * 60)
        self.logger.info(f'Vault path: {self.vault_path.absolute()}')
        self.logger.info(f'Check interval: {self.check_interval}s')

        if not self.page_access_token or not self.page_id:
            self.logger.error('Facebook API not configured.')
            self.logger.error('Set FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID in .env file')
            self.logger.error('See FACEBOOK_SETUP.md for instructions')
            return

        self.logger.info('=' * 60)
        self.logger.info('Facebook Watcher is now running...')
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
        description='Facebook Watcher - Monitor Facebook using Graph API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python facebook_watcher.py .
  python facebook_watcher.py . --interval 300 --keywords "urgent,message,inquiry"

Setup:
  1. Create Facebook App at developers.facebook.com
  2. Get Page Access Token
  3. Set FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID in .env
        """
    )
    parser.add_argument('vault_path', nargs='?', default='.', help='Path to Obsidian vault')
    parser.add_argument('--interval', '-i', type=int, default=300, help='Check interval in seconds (default: 300)')
    parser.add_argument('--keywords', '-k', type=str, default='', help='Comma-separated keywords to filter')
    parser.add_argument('--page-token', type=str, help='Facebook Page Access Token')
    parser.add_argument('--page-id', type=str, help='Facebook Page ID')

    args = parser.parse_args()

    # Parse keywords
    keywords = [k.strip() for k in args.keywords.split(',')] if args.keywords else None

    watcher = FacebookWatcher(
        vault_path=args.vault_path,
        page_access_token=args.page_token,
        page_id=args.page_id,
        check_interval=args.interval,
        keywords=keywords
    )
    watcher.run()


if __name__ == "__main__":
    main()
