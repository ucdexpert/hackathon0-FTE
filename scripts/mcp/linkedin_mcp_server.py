#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn MCP Server for Qwen Code Integration
Provides Model Context Protocol interface for LinkedIn operations.

Usage:
    python server.py  # Runs as stdio MCP server

Features:
    - Post to LinkedIn
    - Check authentication status
    - Human-in-the-loop approval workflow
    - Audit logging
"""

import sys
import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("Install Playwright first:")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)

# ─────────────────────────────────────────────
#  LOGGING SETUP
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
log = logging.getLogger("linkedin-mcp")

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
VAULT_DIR = SCRIPT_DIR.parent.parent
SESSION_PATH = VAULT_DIR / ".linkedin_session"
LOGS_DIR = VAULT_DIR / "Logs"
PENDING_APPROVAL = VAULT_DIR / "Pending_Approval"
APPROVED_DIR = VAULT_DIR / "Approved"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
APPROVED_DIR.mkdir(parents=True, exist_ok=True)

# MCP Protocol Constants
MCP_VERSION = "2024-11-05"
SERVER_NAME = "linkedin-mcp"
SERVER_VERSION = "1.0.0"

# ─────────────────────────────────────────────
#  LINKEDIN CLIENT
# ─────────────────────────────────────────────
class LinkedInClient:
    """Handles all LinkedIn browser automation."""

    def __init__(self, session_path: Optional[Path] = None):
        self.session_path = session_path or SESSION_PATH
        self.session_path.mkdir(parents=True, exist_ok=True)

    def _get_browser(self, p, headless: bool = True):
        """Create browser context with anti-detection."""
        return p.chromium.launch_persistent_context(
            str(self.session_path),
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
            viewport={"width": 1280, "height": 900},
            timeout=60_000,
        )

    def is_authenticated(self) -> bool:
        """Check if session exists."""
        return self.session_path.exists() and any(self.session_path.iterdir())

    def authenticate(self) -> Dict[str, Any]:
        """
        Open browser for manual login.
        Returns status dict for MCP response.
        """
        log.info("Starting authentication flow...")

        try:
            with sync_playwright() as p:
                browser = self._get_browser(p, headless=False)
                page = browser.pages[0] if browser.pages else browser.new_page()

                log.info("Navigate to LinkedIn login...")
                page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")

                # Wait for user to login (5 min timeout)
                deadline = time.time() + 300
                while time.time() < deadline:
                    time.sleep(2)
                    url = page.url
                    if "feed" in url or ("linkedin.com" in url and "login" not in url):
                        log.info("Login detected!")
                        time.sleep(2)
                        browser.close()
                        return {
                            "success": True,
                            "message": "Authentication successful. Session saved.",
                            "session_path": str(self.session_path)
                        }

                browser.close()
                return {
                    "success": False,
                    "message": "Authentication timed out. Please try again."
                }

        except Exception as e:
            log.error(f"Authentication error: {e}")
            return {
                "success": False,
                "message": f"Authentication failed: {str(e)}"
            }

    def post(self, content: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        Post content to LinkedIn.
        Returns status dict with result.
        """
        log.info(f"Posting to LinkedIn (dry_run={dry_run}): {content[:80]}...")

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "message": "Dry run - post not submitted",
                "content": content,
                "content_length": len(content)
            }

        if not self.is_authenticated():
            return {
                "success": False,
                "error": "Not authenticated",
                "message": "Run authenticate tool first"
            }

        try:
            with sync_playwright() as p:
                # Use headed mode (headless=False) so user can see what's happening
                browser = self._get_browser(p, headless=False)
                page = browser.pages[0] if browser.pages else browser.new_page()

                # Step 1: Navigate to feed
                log.info("Step 1/4: Loading LinkedIn feed...")
                page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60_000)
                time.sleep(5)

                # Step 2: Open post creator using JS (most reliable)
                log.info("Step 2/4: Opening post creator...")
                page.evaluate("""
                    () => {
                        const btn = Array.from(document.querySelectorAll('button'))
                            .find(b => b.textContent.includes('Start a post'));
                        if (btn) btn.click();
                    }
                """)
                time.sleep(3)

                # Step 3: Type content using improved editor detection
                log.info("Step 3/4: Typing content...")

                # Save debug screenshot before typing
                debug_path = LOGS_DIR / f"linkedin_debug_{int(time.time())}.png"
                try:
                    page.screenshot(path=str(debug_path))
                    log.debug(f"Debug screenshot saved: {debug_path}")
                except Exception as e:
                    log.debug(f"Could not save debug screenshot: {e}")

                # Wait for editor to be ready
                time.sleep(2)

                # Method 1: Use keyboard to type (most reliable for LinkedIn)
                typed = False
                try:
                    # Find and focus the editor using multiple selector strategies
                    editor = None
                    
                    # Try finding by role and accessibility labels first
                    editor_selectors = [
                        "div[contenteditable='true'][role='textbox']",
                        "div[contenteditable='true']",
                        "[data-placeholder*='share']",
                        "[data-placeholder*='post']",
                        "[aria-label*='post']",
                        ".share-box-feed-entry__dialog",
                    ]
                    
                    for selector in editor_selectors:
                        try:
                            editor = page.query_selector(selector)
                            if editor and editor.is_visible():
                                log.info(f"Found editor with selector: {selector}")
                                break
                        except:
                            continue
                    
                    # If found via query_selector, use keyboard typing
                    if editor:
                        editor.click()
                        time.sleep(1)
                        
                        # Clear any existing content
                        page.keyboard.press("Control+A")
                        time.sleep(0.2)
                        
                        # Type the content using keyboard
                        page.keyboard.type(content, delay=30)
                        time.sleep(1)
                        
                        # Verify content was entered
                        typed_text = page.evaluate("""
                            () => {
                                const editor = document.querySelector('div[contenteditable="true"]:focus');
                                return editor ? editor.innerText : '';
                            }
                        """)
                        
                        if typed_text and len(typed_text) > len(content) * 0.5:
                            typed = True
                            log.info(f"Successfully typed {len(typed_text)} characters via keyboard")
                    
                except Exception as e:
                    log.warning(f"Keyboard typing failed: {e}")

                # Method 2: Fallback to JavaScript injection
                if not typed:
                    log.info("Trying JavaScript injection fallback...")
                    
                    result = page.evaluate("""
                        (text) => {
                            // Strategy 1: Find focused or most recent contenteditable
                            let editor = document.activeElement;
                            if (editor && editor.getAttribute('contenteditable') === 'true') {
                                editor.innerText = text;
                                editor.dispatchEvent(new InputEvent('input', { bubbles: true }));
                                console.log('Typed in focused editor');
                                return true;
                            }

                            // Strategy 2: Find all contenteditable divs
                            const editors = Array.from(document.querySelectorAll('div[contenteditable="true"]'));
                            
                            // Try to find by placeholder
                            for (let el of editors) {
                                const placeholder = el.getAttribute('data-placeholder') || '';
                                if (placeholder.toLowerCase().includes('share') || 
                                    placeholder.toLowerCase().includes('post')) {
                                    el.innerText = text;
                                    el.dispatchEvent(new InputEvent('input', { bubbles: true }));
                                    console.log('Typed by placeholder match');
                                    return true;
                                }
                            }
                            
                            // Strategy 3: Use first visible contenteditable
                            for (let el of editors) {
                                if (el.offsetParent !== null && el.checkVisibility()) {
                                    el.innerText = text;
                                    el.dispatchEvent(new InputEvent('input', { bubbles: true }));
                                    console.log('Typed in first visible editor');
                                    return true;
                                }
                            }
                            
                            // Strategy 4: Try textarea
                            const textareas = document.querySelectorAll('textarea');
                            for (let ta of textareas) {
                                if (ta.offsetParent !== null && ta.checkVisibility()) {
                                    ta.value = text;
                                    ta.dispatchEvent(new InputEvent('input', { bubbles: true }));
                                    console.log('Typed in textarea');
                                    return true;
                                }
                            }
                            
                            console.log('No editor found - total contenteditable:', editors.length);
                            return false;
                        }
                    """, content)
                    
                    typed = result

                if not typed:
                    # Save HTML for debugging
                    html_path = LOGS_DIR / f"linkedin_debug_{int(time.time())}.html"
                    html_path.write_text(page.content(), encoding="utf-8")
                    log.info(f"Page HTML saved to: {html_path}")
                    raise RuntimeError("Could not find editor. Debug files saved to Logs/")

                time.sleep(2)

                # Step 4: Click Post button
                log.info("Step 4/4: Submitting post...")
                page.evaluate("""
                    () => {
                        const btn = Array.from(document.querySelectorAll('button'))
                            .find(b => b.textContent.trim() === 'Post' && !b.disabled);
                        if (btn) btn.click();
                    }
                """)

                # Wait and screenshot
                time.sleep(5)
                screenshot_path = LOGS_DIR / f"linkedin_post_{int(time.time())}.png"
                page.screenshot(path=str(screenshot_path))

                browser.close()

                return {
                    "success": True,
                    "message": "Post submitted successfully",
                    "screenshot": str(screenshot_path),
                    "timestamp": datetime.now().isoformat(),
                    "content_length": len(content)
                }

        except Exception as e:
            log.error(f"Post failed: {e}")
            return {
                "success": False,
                "error": "Post failed",
                "message": str(e)
            }

    def _open_post_creator(self, page) -> bool:
        """Click 'Start a post' button."""
        selectors = [
            "button.share-box-feed-entry__trigger",
            "[data-control-name='share.sharebox_trigger']",
            "button[aria-label*='post']",
            "button[aria-label*='Post']",
        ]

        for sel in selectors:
            try:
                btn = page.wait_for_selector(sel, timeout=3_000, state="visible")
                if btn:
                    btn.click()
                    log.info(f"Clicked via: {sel}")
                    return True
            except Exception:
                continue

        # JS fallback
        result = page.evaluate("""
            () => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const btn = buttons.find(b =>
                    b.textContent.includes('Start a post') ||
                    (b.getAttribute('aria-label') || '').toLowerCase().includes('post')
                );
                if (btn) { btn.click(); return true; }
                return false;
            }
        """)

        if result:
            log.info("Clicked via JS fallback")
            return True

        raise RuntimeError("Could not open post creator")

    def _type_content(self, page, content: str):
        """Type content into editor."""
        # Wait for modal to fully render
        time.sleep(3)
        
        # Save screenshot for debugging
        debug_path = LOGS_DIR / f"linkedin_debug_{int(time.time())}.png"
        try:
            page.screenshot(path=str(debug_path))
            log.info(f"Debug screenshot saved: {debug_path}")
        except Exception as e:
            log.warning(f"Could not save debug screenshot: {e}")

        editor_selectors = [
            "div[contenteditable='true'][role='textbox']",
            "div[contenteditable='true']",
            ".ql-editor",
            "div[data-placeholder*='What do you want to share?']",
            "div[data-placeholder*='post']",
            "div[data-placeholder*='Post']",
            "[aria-label*='What do you want to share']",
        ]

        editor = None
        for sel in editor_selectors:
            try:
                el = page.query_selector(sel)
                if el:
                    # Check if element is visible and enabled
                    if el.is_visible():
                        editor = el
                        log.info(f"Editor found via: {sel}")
                        break
            except Exception as e:
                log.debug(f"Selector {sel} failed: {e}")
                continue

        if not editor:
            # Try JS fallback - find any contenteditable div
            log.info("Trying JS fallback to find editor...")
            editor_info = page.evaluate("""
                () => {
                    const editors = Array.from(document.querySelectorAll('div[contenteditable="true"]'));
                    for (const el of editors) {
                        if (el.offsetParent !== null && el.checkVisibility()) {
                            return { found: true, placeholder: el.getAttribute('data-placeholder') };
                        }
                    }
                    return { found: false };
                }
            """)
            log.info(f"JS fallback result: {editor_info}")
            
            if not editor_info.get('found'):
                # Save full page HTML for debugging
                html_path = LOGS_DIR / f"linkedin_debug_{int(time.time())}.html"
                html_path.write_text(page.content(), encoding="utf-8")
                log.info(f"Page HTML saved: {html_path}")
                
            raise RuntimeError(f"Editor not found. Debug files saved to Logs/")

        editor.click()
        time.sleep(1)
        
        # Clear any existing content
        page.keyboard.press("Control+a")
        time.sleep(0.3)
        page.keyboard.press("Backspace")
        time.sleep(0.3)
        
        # Type content
        page.keyboard.type(content, delay=50)
        time.sleep(1)
        
        # Verify content was typed
        typed = editor.inner_text()
        if not typed or len(typed) < len(content) * 0.8:
            log.warning(f"Content verification failed. Expected {len(content)} chars, got {len(typed)}")
            # Try fill as fallback
            editor.fill(content)
            time.sleep(1)
        
        log.info(f"Typed {len(content)} characters ✓")

    def _submit_post(self, page):
        """Click Post button."""
        selectors = [
            "button.share-actions__primary-action",
            "button[data-control-name='share.post']",
            "button:has-text('Post')",
            "button:has-text('Share')",
        ]

        for sel in selectors:
            try:
                btn = page.wait_for_selector(sel, timeout=3_000, state="visible")
                if btn and not page.evaluate(f"document.querySelector('{sel}')?.disabled"):
                    btn.click()
                    log.info(f"Submitted via: {sel}")
                    return
            except Exception:
                continue

        # Fallback: Ctrl+Enter
        log.warning("Using Ctrl+Enter fallback")
        page.keyboard.press("Control+Enter")


# ─────────────────────────────────────────────
#  MCP SERVER
# ─────────────────────────────────────────────
class MCPServer:
    """MCP Protocol Server for LinkedIn operations."""

    def __init__(self):
        self.client = LinkedInClient()
        self.tools = self._define_tools()

    def _define_tools(self) -> List[Dict]:
        """Define available MCP tools."""
        return [
            {
                "name": "linkedin_authenticate",
                "description": "Open browser for manual LinkedIn login. Session is saved for future use.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "linkedin_check_auth",
                "description": "Check if LinkedIn session is authenticated.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "linkedin_post",
                "description": "Post content to LinkedIn. Requires prior authentication.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The post content (max 3000 characters)"
                        },
                        "dry_run": {
                            "type": "boolean",
                            "description": "If true, log but don't actually post"
                        }
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "linkedin_create_approval_request",
                "description": "Create a Human-in-the-Loop approval request file for a LinkedIn post.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The post content to approve"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for this post"
                        }
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "linkedin_check_approvals",
                "description": "Check for approved LinkedIn post requests in /Approved folder.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]

    def handle_request(self, request: Dict) -> Dict:
        """Handle incoming MCP request."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        log.info(f"Received: {method}")

        try:
            if method == "initialize":
                return self._response(request_id, {
                    "protocolVersion": MCP_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION
                    }
                })

            elif method == "tools/list":
                return self._response(request_id, {"tools": self.tools})

            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                return self._handle_tool(request_id, tool_name, tool_args)

            elif method == "notifications/initialized":
                return None  # No response needed for notifications

            else:
                return self._error(request_id, -32601, f"Method not found: {method}")

        except Exception as e:
            log.error(f"Request error: {e}")
            return self._error(request_id, -32603, str(e))

    def _handle_tool(self, request_id: Any, tool_name: str, args: Dict) -> Dict:
        """Execute tool call and return result."""

        if tool_name == "linkedin_authenticate":
            result = self.client.authenticate()
            return self._response(request_id, {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
            })

        elif tool_name == "linkedin_check_auth":
            is_auth = self.client.is_authenticated()
            return self._response(request_id, {
                "content": [{
                    "type": "text",
                    "text": f"LinkedIn authentication: {'✓ AUTHENTICATED' if is_auth else '✗ NOT AUTHENTICATED'}\n\n"
                            f"Session path: {self.client.session_path}\n\n"
                            f"{'Run linkedin_authenticate to login.' if not is_auth else 'Ready to post!'}"
                }]
            })

        elif tool_name == "linkedin_post":
            content = args.get("content", "")
            dry_run = args.get("dry_run", False)

            if not content:
                return self._error(request_id, -32000, "Content is required")

            if len(content) > 3000:
                return self._error(request_id, -32000, "Content exceeds 3000 characters")

            result = self.client.post(content, dry_run=dry_run)
            return self._response(request_id, {
                "content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]
            })

        elif tool_name == "linkedin_create_approval_request":
            content = args.get("content", "")
            reason = args.get("reason", "LinkedIn post")

            filename = f"LINKEDIN_POST_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            filepath = PENDING_APPROVAL / filename

            md_content = f"""---
type: linkedin_post_approval
action: post_to_linkedin
content_length: {len(content)}
created: {datetime.now().isoformat()}
status: pending
reason: {reason}
---

## LinkedIn Post Content

{content}

## To Approve
Move this file to: /Approved/

## To Reject
Move this file to: /Rejected/

## Auto-Posted By
LinkedIn MCP Server will post when approved.
"""
            filepath.write_text(md_content, encoding="utf-8")

            return self._response(request_id, {
                "content": [{
                    "type": "text",
                    "text": f"✓ Approval request created: {filepath}\n\n"
                            f"Move to /Approved/ to execute the post."
                }]
            })

        elif tool_name == "linkedin_check_approvals":
            approved_files = list(APPROVED_DIR.glob("LINKEDIN_POST_*.md"))

            if not approved_files:
                return self._response(request_id, {
                    "content": [{"type": "text", "text": "No approved LinkedIn posts pending."}]
                })

            files_info = []
            for f in approved_files:
                files_info.append(f.name)

            return self._response(request_id, {
                "content": [{
                    "type": "text",
                    "text": f"Found {len(approved_files)} approved post(s):\n\n" +
                            "\n".join(f"  - {f}" for f in files_info)
                }]
            })

        else:
            return self._error(request_id, -32000, f"Unknown tool: {tool_name}")

    def _response(self, request_id: Any, result: Any) -> Dict:
        """Create JSON-RPC response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

    def _error(self, request_id: Any, code: int, message: str) -> Dict:
        """Create JSON-RPC error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }

    def run_stdio(self):
        """Run as stdio MCP server."""
        log.info("LinkedIn MCP Server starting (stdio mode)...")

        buffer = ""
        for line in sys.stdin:
            buffer += line
            if buffer.endswith("\n"):
                try:
                    request = json.loads(buffer)
                    response = self.handle_request(request)
                    if response:
                        print(json.dumps(response), flush=True)
                except json.JSONDecodeError:
                    log.warning(f"Invalid JSON: {buffer[:100]}")
                buffer = ""


# ─────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────
def main():
    import argparse

    parser = argparse.ArgumentParser(description="LinkedIn MCP Server")
    parser.add_argument("--authenticate", "-a", action="store_true",
                        help="Run authentication flow")
    parser.add_argument("--check-auth", action="store_true",
                        help="Check authentication status")
    parser.add_argument("--post", "-p", type=str, help="Post content")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--stdio", action="store_true", help="Run as stdio server")

    args = parser.parse_args()

    server = MCPServer()

    if args.stdio:
        server.run_stdio()
    elif args.check_auth:
        is_auth = server.client.is_authenticated()
        print(f"\nLinkedIn Authentication: {'✓ AUTHENTICATED' if is_auth else '✗ NOT AUTHENTICATED'}")
        print(f"Session: {server.client.session_path}\n")
    elif args.authenticate:
        result = server.client.authenticate()
        print(json.dumps(result, indent=2))
    elif args.post:
        result = server.client.post(args.post, dry_run=args.dry_run)
        print(json.dumps(result, indent=2, default=str))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
