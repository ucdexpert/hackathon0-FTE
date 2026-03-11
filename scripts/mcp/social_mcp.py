#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Social Media MCP Server - Facebook (Graph API) and Instagram integration.

Provides MCP tools for:
- facebook_post: Post to Facebook Page (requires HITL approval)
- facebook_post_photo: Post photo to Facebook Page
- facebook_reply_comment: Reply to a comment
- instagram_post: Post to Instagram (requires HITL approval)
- get_facebook_insights: Get Facebook page insights
- get_instagram_insights: Get Instagram insights
- schedule_post: Schedule a social media post

Usage:
    python social_mcp.py [--port PORT]
"""

import sys
import json
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP library not installed. Install with: pip install mcp")


class SocialMediaMCPServer:
    """MCP Server for Facebook (Graph API) and Instagram operations."""

    def __init__(self, vault_path: str = '.'):
        """
        Initialize Social Media MCP Server.

        Args:
            vault_path: Path to Obsidian vault for HITL workflow
        """
        self.vault_path = Path(vault_path)

        # Load Facebook configuration from environment
        load_dotenv()
        self.page_access_token = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
        self.page_id = os.getenv('FACEBOOK_PAGE_ID')
        self.instagram_business_account_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')

        # Facebook Graph API
        self.graph_api_version = 'v18.0'
        self.base_url = f'https://graph.facebook.com/{self.graph_api_version}'

        # HITL folders
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.logs = self.vault_path / 'Logs'
        self.social = self.vault_path / 'Social'

        for folder in [self.pending_approval, self.approved, self.logs, self.social]:
            folder.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(self.__class__.__name__)

    def _make_graph_request(self, endpoint: str, method: str = 'GET',
                            params: Dict = None, data: Dict = None) -> Dict:
        """Make a request to Facebook Graph API."""
        if not self.page_access_token:
            return {'error': {'message': 'Page Access Token not configured'}}

        url = f'{self.base_url}/{endpoint}'
        default_params = {'access_token': self.page_access_token}

        if params:
            default_params.update(params)

        try:
            if method == 'GET':
                response = requests.get(url, params=default_params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, params=default_params, data=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, params=default_params, timeout=30)
            else:
                return {'error': {'message': f'Unsupported method: {method}'}}

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f'Graph API request failed: {e}')
            return {'error': {'message': str(e)}}

    def facebook_post(self, content: str, link: str = None,
                      privacy: str = 'EVERYONE') -> Dict:
        """
        Post to Facebook Page.

        For sensitive actions, creates HITL approval file first.
        """
        if not self.page_access_token or not self.page_id:
            return {'error': 'Facebook API not configured. Set FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID'}

        try:
            # Create approval file for HITL
            approval_file = self._create_social_approval_request(
                platform='facebook',
                action='post',
                content=content,
                link=link,
                privacy=privacy
            )

            return {
                'status': 'pending_approval',
                'approval_file': str(approval_file),
                'message': f'Approval file created: {approval_file.name}'
            }

        except Exception as e:
            self.logger.error(f'Failed to create Facebook post approval: {e}')
            return {'error': str(e)}

    def facebook_post_photo(self, photo_url: str, content: str = '') -> Dict:
        """
        Post photo to Facebook Page.

        For sensitive actions, creates HITL approval file first.
        """
        if not self.page_access_token or not self.page_id:
            return {'error': 'Facebook API not configured'}

        try:
            # Create approval file for HITL
            approval_file = self._create_social_approval_request(
                platform='facebook',
                action='post_photo',
                content=content,
                photo_url=photo_url
            )

            return {
                'status': 'pending_approval',
                'approval_file': str(approval_file),
                'message': f'Approval file created: {approval_file.name}'
            }

        except Exception as e:
            self.logger.error(f'Failed to create Facebook photo post approval: {e}')
            return {'error': str(e)}

    def execute_facebook_post(self, approval_file: Path) -> Dict:
        """Execute an approved Facebook post."""
        try:
            # Read approval file to get post details
            content = approval_file.read_text(encoding='utf-8')

            # Parse content
            post_content = self._extract_post_content(content)
            link = self._extract_link(content)
            photo_url = self._extract_photo_url(content)

            if photo_url:
                # Post photo
                result = self._post_photo_to_facebook(photo_url, post_content)
            else:
                # Post text/link
                result = self._post_text_to_facebook(post_content, link)

            return result

        except Exception as e:
            self.logger.error(f'Failed to execute Facebook post: {e}')
            return {'error': str(e)}

    def _post_text_to_facebook(self, message: str, link: str = None) -> Dict:
        """Post text or link to Facebook Page."""
        endpoint = f'{self.page_id}/feed'

        data = {'message': message}
        if link:
            data['link'] = link

        result = self._make_graph_request(endpoint, method='POST', data=data)

        if 'id' in result:
            self.logger.info(f'Facebook post created: {result["id"]}')
            return {
                'status': 'success',
                'post_id': result['id'],
                'message': 'Post published to Facebook',
                'timestamp': datetime.now().isoformat()
            }

        return result

    def _post_photo_to_facebook(self, photo_url: str, message: str = '') -> Dict:
        """Post photo to Facebook Page."""
        endpoint = f'{self.page_id}/photos'

        data = {
            'url': photo_url,
            'message': message
        }

        result = self._make_graph_request(endpoint, method='POST', data=data)

        if 'id' in result:
            self.logger.info(f'Facebook photo post created: {result["id"]}')
            return {
                'status': 'success',
                'post_id': result['id'],
                'message': 'Photo published to Facebook',
                'timestamp': datetime.now().isoformat()
            }

        return result

    def facebook_reply_comment(self, comment_id: str, message: str) -> Dict:
        """Reply to a Facebook comment."""
        if not self.page_access_token:
            return {'error': 'Facebook API not configured'}

        endpoint = f'{comment_id}/comments'
        data = {'message': message}

        result = self._make_graph_request(endpoint, method='POST', data=data)

        if 'id' in result:
            self.logger.info(f'Facebook comment reply created: {result["id"]}')
            return {
                'status': 'success',
                'comment_id': result['id'],
                'message': 'Reply posted to Facebook'
            }

        return result

    def instagram_post(self, image_url: str, content: str = '',
                       hashtags: List[str] = None) -> Dict:
        """
        Post to Instagram Business Account.

        For sensitive actions, creates HITL approval file first.
        """
        if not self.page_access_token or not self.instagram_business_account_id:
            return {'error': 'Instagram API not configured. Set INSTAGRAM_BUSINESS_ACCOUNT_ID'}

        try:
            # Create approval file for HITL
            approval_file = self._create_social_approval_request(
                platform='instagram',
                action='post',
                content=content,
                image_url=image_url,
                hashtags=hashtags or []
            )

            return {
                'status': 'pending_approval',
                'approval_file': str(approval_file),
                'message': f'Approval file created: {approval_file.name}'
            }

        except Exception as e:
            self.logger.error(f'Failed to create Instagram post approval: {e}')
            return {'error': str(e)}

    def execute_instagram_post(self, approval_file: Path) -> Dict:
        """Execute an approved Instagram post."""
        try:
            # Read approval file to get post details
            content = approval_file.read_text(encoding='utf-8')

            # Parse content
            post_content = self._extract_post_content(content)
            image_url = self._extract_image_url(content)
            hashtags = self._extract_hashtags(content)

            if not image_url:
                return {'error': 'Image URL required for Instagram post'}

            # Combine content and hashtags
            full_caption = post_content
            if hashtags:
                full_caption += '\n\n' + ' '.join(f'#{tag}' for tag in hashtags)

            # Step 1: Create media container
            endpoint = f'{self.instagram_business_account_id}/media'
            data = {
                'image_url': image_url,
                'caption': full_caption
            }

            container_result = self._make_graph_request(endpoint, method='POST', data=data)

            if 'id' not in container_result:
                return container_result

            creation_id = container_result['id']

            # Step 2: Publish the media
            publish_endpoint = f'{self.instagram_business_account_id}/media_publish'
            publish_data = {'creation_id': creation_id}

            publish_result = self._make_graph_request(publish_endpoint, method='POST', data=publish_data)

            if 'id' in publish_result:
                self.logger.info(f'Instagram post created: {publish_result["id"]}')
                return {
                    'status': 'success',
                    'post_id': publish_result['id'],
                    'message': 'Post published to Instagram',
                    'timestamp': datetime.now().isoformat()
                }

            return publish_result

        except Exception as e:
            self.logger.error(f'Failed to execute Instagram post: {e}')
            return {'error': str(e)}

    def get_facebook_insights(self) -> Dict:
        """Get Facebook page insights."""
        if not self.page_access_token or not self.page_id:
            return {'error': 'Facebook API not configured'}

        # Get page insights
        insights_result = self._make_graph_request(
            f'{self.page_id}/insights',
            params={
                'metric': 'page_impressions,page_reach,page_followers,page_likes,post_engagements',
                'period': 'day'
            }
        )

        if 'data' in insights_result:
            insights = {}
            for metric in insights_result['data']:
                name = metric.get('name', 'unknown')
                values = metric.get('values', [])
                if values:
                    insights[name] = values[-1].get('value', 0)

            # Get current follower count
            page_result = self._make_graph_request(
                self.page_id,
                params={'fields': 'followers_count,likes'}
            )

            insights['followers_count'] = page_result.get('followers_count', 0)
            insights['likes'] = page_result.get('likes', 0)

            return {
                'status': 'success',
                'insights': insights,
                'timestamp': datetime.now().isoformat()
            }

        return insights_result

    def get_instagram_insights(self) -> Dict:
        """Get Instagram Business account insights."""
        if not self.page_access_token or not self.instagram_business_account_id:
            return {'error': 'Instagram API not configured'}

        # Get Instagram insights
        insights_result = self._make_graph_request(
            f'{self.instagram_business_account_id}/insights',
            params={
                'metric': 'follower_count,impressions,reach,profile_views'
            }
        )

        if 'data' in insights_result:
            insights = {}
            for metric in insights_result['data']:
                name = metric.get('name', 'unknown')
                values = metric.get('values', [])
                if values:
                    insights[name] = values[-1].get('value', 0)

            return {
                'status': 'success',
                'insights': insights,
                'timestamp': datetime.now().isoformat()
            }

        return insights_result

    def schedule_post(self, platform: str, content: str,
                      schedule_time: str, image_url: str = None) -> Dict:
        """Schedule a social media post for later."""
        try:
            # Create scheduled post file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = self.social / f"SCHEDULED_{platform}_{schedule_time.replace('-', '')}_{timestamp}.md"

            content_md = f"""---
type: scheduled_post
platform: {platform}
scheduled_time: {schedule_time}
created: {datetime.now().isoformat()}
status: scheduled
image_url: {image_url or 'None'}
---

# Scheduled Social Media Post

**Platform:** {platform.title()}

**Scheduled Time:** {schedule_time}

---

## Content

{content}

---

*Created by Social Media MCP Server*
"""
            filepath.write_text(content_md, encoding='utf-8')

            return {
                'status': 'scheduled',
                'file': str(filepath),
                'message': f'Post scheduled for {schedule_time}'
            }

        except Exception as e:
            self.logger.error(f'Failed to schedule post: {e}')
            return {'error': str(e)}

    def _create_social_approval_request(self, platform: str, action: str,
                                         content: str, image_url: str = None,
                                         photo_url: str = None,
                                         link: str = None,
                                         **kwargs) -> Path:
        """Create HITL approval request file for social media post."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = self.pending_approval / f"SOCIAL_{platform.upper()}_{action.upper()}_{timestamp}.md"

        hashtags = kwargs.get('hashtags', [])
        privacy = kwargs.get('privacy', 'EVERYONE')

        content_body = content
        if hashtags:
            content_body += '\n\n' + ' '.join(f'#{tag}' for tag in hashtags)

        post_preview = content[:200] + ('...' if len(content) > 200 else '')

        content_md = f"""---
type: approval_request
action: social_media_post
platform: {platform}
post_action: {action}
created: {datetime.now().isoformat()}
status: pending
image_url: {image_url or photo_url or 'None'}
link: {link or 'None'}
privacy: {privacy}
hashtags: {json.dumps(hashtags)}
---

# Social Media Post Approval Request

**Platform:** {platform.title()}

**Action:** {action.replace('_', ' ').title()}

{f'**Privacy:** {privacy}' if privacy else ''}

---

## Post Content

{content_body}

---

## Preview

{post_preview}

---

## Media

{'![Image](' + (image_url or photo_url) + ')' if (image_url or photo_url) else '*No image attached*'}

{f'**Link:** {link}' if link else ''}

---

## To Approve
Move this file to /Approved folder.

## To Reject
Move this file to /Rejected folder.

---

*Created by Social Media MCP Server (Graph API)*
"""
        filepath.write_text(content_md, encoding='utf-8')
        self.logger.info(f'Created social media approval request: {filepath.name}')
        return filepath

    def _extract_post_content(self, approval_content: str) -> str:
        """Extract post content from approval file."""
        if '## Post Content' in approval_content:
            content = approval_content.split('## Post Content')[1]
            if '---' in content:
                content = content.split('---')[0]
            return content.strip()
        return ''

    def _extract_image_url(self, approval_content: str) -> str:
        """Extract image URL from approval file."""
        if 'image_url:' in approval_content:
            line = [l for l in approval_content.split('\n') if 'image_url:' in l][0]
            path = line.split('image_url:')[1].strip()
            if path and path != 'None':
                return path
        return None

    def _extract_photo_url(self, approval_content: str) -> str:
        """Extract photo URL from approval file."""
        return self._extract_image_url(approval_content)

    def _extract_link(self, approval_content: str) -> str:
        """Extract link from approval file."""
        if 'link:' in approval_content:
            line = [l for l in approval_content.split('\n') if 'link:' in l][0]
            path = line.split('link:')[1].strip()
            if path and path != 'None':
                return path
        return None

    def _extract_hashtags(self, approval_content: str) -> List[str]:
        """Extract hashtags from approval file."""
        if 'hashtags:' in approval_content:
            line = [l for l in approval_content.split('\n') if 'hashtags:' in l][0]
            try:
                hashtags_str = line.split('hashtags:')[1].strip()
                return json.loads(hashtags_str)
            except:
                pass
        return []

    def log_action(self, action_type: str, details: Dict, status: str = 'info'):
        """Log an action to the social media log."""
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs / f'social_{today}.md'

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        entry = f'[{timestamp}] [{status.upper()}] {action_type}: {json.dumps(details)}'

        if log_file.exists():
            content = log_file.read_text(encoding='utf-8')
            content = content.rstrip() + '\n' + entry + '\n'
        else:
            content = f"# Social Media Actions Log - {today}\n\n{entry}\n"

        log_file.write_text(content, encoding='utf-8')


def create_mcp_server_tools(social_server: SocialMediaMCPServer) -> List[Tool]:
    """Create MCP tool definitions."""
    return [
        Tool(
            name="facebook_post",
            description="Post to Facebook Page (requires HITL approval)",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Post content"},
                    "link": {"type": "string", "description": "Link to share (optional)"}
                },
                "required": ["content"]
            }
        ),
        Tool(
            name="facebook_post_photo",
            description="Post photo to Facebook Page (requires HITL approval)",
            inputSchema={
                "type": "object",
                "properties": {
                    "photo_url": {"type": "string", "description": "URL of the photo"},
                    "content": {"type": "string", "description": "Caption for the photo"}
                },
                "required": ["photo_url"]
            }
        ),
        Tool(
            name="facebook_reply_comment",
            description="Reply to a Facebook comment",
            inputSchema={
                "type": "object",
                "properties": {
                    "comment_id": {"type": "string", "description": "Facebook comment ID"},
                    "message": {"type": "string", "description": "Reply message"}
                },
                "required": ["comment_id", "message"]
            }
        ),
        Tool(
            name="instagram_post",
            description="Post to Instagram Business Account (requires HITL approval)",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_url": {"type": "string", "description": "URL of the image"},
                    "content": {"type": "string", "description": "Post caption"},
                    "hashtags": {"type": "array", "items": {"type": "string"}, "description": "Hashtags (without #)"}
                },
                "required": ["image_url", "content"]
            }
        ),
        Tool(
            name="get_facebook_insights",
            description="Get Facebook Page insights (impressions, reach, followers)",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_instagram_insights",
            description="Get Instagram Business account insights",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="schedule_post",
            description="Schedule a social media post for later",
            inputSchema={
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "description": "Platform (facebook, instagram)"},
                    "content": {"type": "string", "description": "Post content"},
                    "schedule_time": {"type": "string", "description": "Schedule time (YYYY-MM-DD HH:MM)"},
                    "image_url": {"type": "string", "description": "URL of image to post"}
                },
                "required": ["platform", "content", "schedule_time"]
            }
        )
    ]


async def run_mcp_server(social_server: SocialMediaMCPServer):
    """Run MCP server using stdio transport."""
    if not MCP_AVAILABLE:
        print("MCP library not available")
        return

    server = Server("social-media-mcp")
    tools = create_mcp_server_tools(social_server)

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict) -> List[TextContent]:
        try:
            if name == "facebook_post":
                result = social_server.facebook_post(
                    content=arguments.get('content'),
                    link=arguments.get('link')
                )
            elif name == "facebook_post_photo":
                result = social_server.facebook_post_photo(
                    photo_url=arguments.get('photo_url'),
                    content=arguments.get('content')
                )
            elif name == "facebook_reply_comment":
                result = social_server.facebook_reply_comment(
                    comment_id=arguments.get('comment_id'),
                    message=arguments.get('message')
                )
            elif name == "instagram_post":
                result = social_server.instagram_post(
                    content=arguments.get('content'),
                    image_url=arguments.get('image_url'),
                    hashtags=arguments.get('hashtags')
                )
            elif name == "get_facebook_insights":
                result = social_server.get_facebook_insights()
            elif name == "get_instagram_insights":
                result = social_server.get_instagram_insights()
            elif name == "schedule_post":
                result = social_server.schedule_post(
                    platform=arguments.get('platform'),
                    content=arguments.get('content'),
                    schedule_time=arguments.get('schedule_time'),
                    image_url=arguments.get('image_url')
                )
            else:
                result = {'error': f'Unknown tool: {name}'}

            # Log action
            social_server.log_action(name, arguments)

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            error_result = {'error': str(e)}
            social_server.log_action(name, arguments, 'error')
            return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Social Media MCP Server (Facebook Graph API)')
    parser.add_argument('--vault', type=str, default='.', help='Path to vault')

    args = parser.parse_args()

    social_server = SocialMediaMCPServer(
        vault_path=args.vault
    )

    if not MCP_AVAILABLE:
        print('MCP library not installed.')
        print('Install: pip install mcp')
        sys.exit(1)

    import asyncio
    print(f'Starting Social Media MCP Server (Graph API)...')
    print(f'Facebook Page ID: {social_server.page_id or "Not configured"}')
    print(f'Instagram Account: {social_server.instagram_business_account_id or "Not configured"}')
    asyncio.run(run_mcp_server(social_server))


if __name__ == "__main__":
    main()
