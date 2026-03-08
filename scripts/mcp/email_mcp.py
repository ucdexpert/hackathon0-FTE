#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email MCP Server - Gmail API integration for sending emails.

Provides MCP tools for:
- send_email: Send an email (requires HITL approval)
- draft_email: Create draft without sending
- search_emails: Search Gmail for messages
- get_email: Get full email by ID

Usage:
    python email_mcp.py [--port PORT] [--authenticate]
"""

import sys
import json
import base64
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP library not installed. Install with: pip install mcp")


class EmailMCPServer:
    """MCP Server for Gmail email operations."""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.send', 
              'https://www.googleapis.com/auth/gmail.readonly',
              'https://www.googleapis.com/auth/gmail.compose']
    
    def __init__(self, credentials_path: str = 'credentials.json', 
                 token_path: str = 'token.json',
                 vault_path: str = '.'):
        """
        Initialize Email MCP Server.
        
        Args:
            credentials_path: Path to Gmail API credentials.json
            token_path: Path to store OAuth token
            vault_path: Path to Obsidian vault for HITL workflow
        """
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.vault_path = Path(vault_path)
        self.service = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # HITL folders
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.pending_approval.mkdir(parents=True, exist_ok=True)
        self.approved.mkdir(parents=True, exist_ok=True)
    
    def authenticate(self) -> bool:
        """Authenticate with Gmail API."""
        if not GOOGLE_LIBS_AVAILABLE:
            self.logger.error('Google libraries not installed')
            return False
        
        try:
            creds = None
            
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not self.credentials_path.exists():
                        self.logger.error(f'Credentials not found: {self.credentials_path}')
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    creds = flow.run_local_server(port=8080)
                
                self.token_path.write_text(creds.to_json())
            
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info('Gmail API authenticated')
            return True
            
        except Exception as e:
            self.logger.error(f'Authentication failed: {e}')
            return False
    
    def _create_message(self, to: str, subject: str, body: str, 
                        html: bool = False, attachments: List[str] = None,
                        cc: List[str] = None, bcc: List[str] = None) -> Dict:
        """Create email message."""
        message = MIMEMultipart() if attachments else MIMEText(body, 'html' if html else 'plain')
        
        if attachments:
            message.attach(MIMEText(body, 'html' if html else 'plain'))
        
        message['to'] = to
        message['subject'] = subject
        
        if cc:
            message['cc'] = ', '.join(cc)
        if bcc:
            message['bcc'] = ', '.join(bcc)
        
        # Add attachments
        for filepath in (attachments or []):
            try:
                with open(filepath, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{Path(filepath).name}"'
                    )
                    message.attach(part)
            except Exception as e:
                self.logger.error(f'Failed to attach {filepath}: {e}')
        
        return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
    
    def send_email(self, to: str, subject: str, body: str,
                   html: bool = False, attachments: List[str] = None,
                   cc: List[str] = None, bcc: List[str] = None,
                   skip_approval: bool = False) -> Dict:
        """
        Send an email via Gmail API.
        
        For sensitive actions, creates HITL approval file first.
        """
        if not self.service:
            if not self.authenticate():
                return {'error': 'Authentication failed'}
        
        try:
            # Create approval file for HITL (unless skipped)
            if not skip_approval:
                approval_file = self._create_approval_request(
                    to=to, subject=subject, body=body,
                    attachments=attachments, cc=cc, bcc=bcc
                )
                return {
                    'status': 'pending_approval',
                    'approval_file': str(approval_file),
                    'message': f'Approval file created: {approval_file.name}'
                }
            
            # Send directly (only for approved actions)
            message = self._create_message(to, subject, body, html, attachments, cc, bcc)
            sent_message = self.service.users().messages().send(
                userId='me', body=message
            ).execute()
            
            self.logger.info(f'Email sent to {to}, ID: {sent_message["id"]}')
            
            return {
                'status': 'sent',
                'message_id': sent_message['id'],
                'thread_id': sent_message.get('threadId')
            }
            
        except HttpError as e:
            self.logger.error(f'Gmail API error: {e}')
            return {'error': str(e)}
        except Exception as e:
            self.logger.error(f'Failed to send email: {e}')
            return {'error': str(e)}
    
    def _create_approval_request(self, to: str, subject: str, body: str,
                                  attachments: List[str] = None,
                                  cc: List[str] = None,
                                  bcc: List[str] = None) -> Path:
        """Create HITL approval request file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_subject = "".join(c if c.isalnum() else "_" for c in subject)[:30]
        filepath = self.pending_approval / f"EMAIL_SEND_{safe_subject}_{timestamp}.md"
        
        content = f"""---
type: approval_request
action: send_email
to: {to}
subject: {subject}
created: {datetime.now().isoformat()}
status: pending
attachments: {json.dumps(attachments or [])}
---

# Email Approval Request

**To:** {to}

**Subject:** {subject}

{f'**CC:** {", ".join(cc)}' if cc else ''}
{f'**BCC:** {", ".join(bcc)}' if bcc else ''}

---

## Email Body

{body}

---

## Attachments

{chr(10).join(f'- {att}' for att in (attachments or ['None']))}

---

## To Approve
Move this file to /Approved folder.

## To Reject
Move this file to /Rejected folder.

---

*Created by Email MCP Server*
"""
        filepath.write_text(content, encoding='utf-8')
        self.logger.info(f'Created approval request: {filepath.name}')
        return filepath
    
    def draft_email(self, to: str, subject: str, body: str,
                    html: bool = False) -> Dict:
        """Create a draft email without sending."""
        if not self.service:
            if not self.authenticate():
                return {'error': 'Authentication failed'}
        
        try:
            message = MIMEText(body, 'html' if html else 'plain')
            message['to'] = to
            message['subject'] = subject
            
            draft_body = {'message': {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}}
            
            draft = self.service.users().drafts().create(
                userId='me', body=draft_body
            ).execute()
            
            self.logger.info(f'Draft created, ID: {draft["id"]}')
            
            return {
                'status': 'draft_created',
                'draft_id': draft['id'],
                'message': f'Draft created successfully'
            }
            
        except Exception as e:
            self.logger.error(f'Failed to create draft: {e}')
            return {'error': str(e)}
    
    def search_emails(self, query: str, max_results: int = 10) -> Dict:
        """Search Gmail for messages."""
        if not self.service:
            if not self.authenticate():
                return {'error': 'Authentication failed'}
        
        try:
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            return {
                'status': 'success',
                'count': len(messages),
                'messages': [{'id': m['id'], 'threadId': m.get('threadId')} for m in messages]
            }
            
        except Exception as e:
            self.logger.error(f'Search failed: {e}')
            return {'error': str(e)}
    
    def get_email(self, message_id: str) -> Dict:
        """Get full email by ID."""
        if not self.service:
            if not self.authenticate():
                return {'error': 'Authentication failed'}
        
        try:
            message = self.service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()
            
            # Extract headers
            headers = message.get('payload', {}).get('headers', [])
            email_data = {'id': message_id}
            
            for header in headers:
                name = header['name'].lower()
                value = header['value']
                if name in ['from', 'to', 'subject', 'date']:
                    email_data[name] = value
            
            email_data['snippet'] = message.get('snippet', '')
            email_data['threadId'] = message.get('threadId')
            
            return {
                'status': 'success',
                'email': email_data
            }
            
        except Exception as e:
            self.logger.error(f'Failed to get email: {e}')
            return {'error': str(e)}


def create_mcp_server_tools(email_server: EmailMCPServer) -> List[Tool]:
    """Create MCP tool definitions."""
    return [
        Tool(
            name="send_email",
            description="Send an email via Gmail (creates HITL approval request)",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body text"},
                    "html": {"type": "boolean", "description": "Is body HTML?", "default": False},
                    "attachments": {"type": "array", "items": {"type": "string"}, "description": "File paths to attach"},
                    "cc": {"type": "array", "items": {"type": "string"}, "description": "CC recipients"},
                    "bcc": {"type": "array", "items": {"type": "string"}, "description": "BCC recipients"}
                },
                "required": ["to", "subject", "body"]
            }
        ),
        Tool(
            name="draft_email",
            description="Create a draft email without sending",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body text"},
                    "html": {"type": "boolean", "description": "Is body HTML?", "default": False}
                },
                "required": ["to", "subject", "body"]
            }
        ),
        Tool(
            name="search_emails",
            description="Search Gmail for messages",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Gmail search query"},
                    "maxResults": {"type": "integer", "description": "Max results to return", "default": 10}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_email",
            description="Get full email details by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {"type": "string", "description": "Gmail message ID"}
                },
                "required": ["message_id"]
            }
        )
    ]


async def run_mcp_server(email_server: EmailMCPServer):
    """Run MCP server using stdio transport."""
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent
    
    server = Server("email-mcp")
    tools = create_mcp_server_tools(email_server)
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return tools
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict) -> List[TextContent]:
        try:
            if name == "send_email":
                result = email_server.send_email(
                    to=arguments.get('to'),
                    subject=arguments.get('subject'),
                    body=arguments.get('body'),
                    html=arguments.get('html', False),
                    attachments=arguments.get('attachments'),
                    cc=arguments.get('cc'),
                    bcc=arguments.get('bcc')
                )
            elif name == "draft_email":
                result = email_server.draft_email(
                    to=arguments.get('to'),
                    subject=arguments.get('subject'),
                    body=arguments.get('body'),
                    html=arguments.get('html', False)
                )
            elif name == "search_emails":
                result = email_server.search_emails(
                    query=arguments.get('query'),
                    max_results=arguments.get('maxResults', 10)
                )
            elif name == "get_email":
                result = email_server.get_email(
                    message_id=arguments.get('message_id')
                )
            else:
                result = {'error': f'Unknown tool: {name}'}
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({'error': str(e)}, indent=2))]
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Email MCP Server')
    parser.add_argument('--port', type=int, default=8809, help='Server port')
    parser.add_argument('--credentials', type=str, default='credentials.json', help='Path to credentials.json')
    parser.add_argument('--vault', type=str, default='.', help='Path to vault')
    parser.add_argument('--authenticate', action='store_true', help='Run authentication only')
    
    args = parser.parse_args()
    
    if not GOOGLE_LIBS_AVAILABLE:
        print('Google libraries not installed.')
        print('Install: pip install google-auth google-auth-oauthlib google-api-python-client')
        sys.exit(1)
    
    email_server = EmailMCPServer(
        credentials_path=args.credentials,
        vault_path=args.vault
    )
    
    if args.authenticate:
        if email_server.authenticate():
            print('Authentication successful!')
            sys.exit(0)
        else:
            print('Authentication failed!')
            sys.exit(1)
    
    if not MCP_AVAILABLE:
        print('MCP library not installed.')
        print('Install: pip install mcp')
        sys.exit(1)
    
    import asyncio
    print(f'Starting Email MCP Server...')
    asyncio.run(run_mcp_server(email_server))


if __name__ == "__main__":
    main()
