#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Post Orchestrator
Processes approved LinkedIn posts and executes them via MCP server.

Usage:
    python linkedin_orchestrator.py              # Process all approved posts
    python linkedin_orchestrator.py --watch      # Continuous watch mode
    python linkedin_orchestrator.py --dry-run    # Log only, don't post
"""

import sys
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add parent directories to path
SCRIPT_DIR = Path(__file__).parent.resolve()
MCP_DIR = SCRIPT_DIR / "mcp"
VAULT_DIR = SCRIPT_DIR.parent

sys.path.insert(0, str(MCP_DIR))

try:
    from linkedin_mcp_server import MCPServer
except ImportError as e:
    print(f"Error importing MCP server: {e}")
    print(f"Make sure linkedin_mcp_server.py exists in: {MCP_DIR}")
    sys.exit(1)

# ─────────────────────────────────────────────
#  LOGGING SETUP
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(VAULT_DIR / "Logs" / "linkedin_orchestrator.log")
    ]
)
log = logging.getLogger("linkedin_orchestrator")

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
APPROVED_DIR = VAULT_DIR / "Approved"
DONE_DIR = VAULT_DIR / "Done"
REJECTED_DIR = VAULT_DIR / "Rejected"
LOGS_DIR = VAULT_DIR / "Logs"

for folder in [APPROVED_DIR, DONE_DIR, REJECTED_DIR, LOGS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
#  LINKEDIN ORCHESTRATOR
# ─────────────────────────────────────────────
class LinkedInOrchestrator:
    """
    Orchestrates LinkedIn posting workflow.
    Implements Human-in-the-Loop pattern from hackathon architecture.
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.server = MCPServer()
        self.processed_count = 0
        self.error_count = 0

    def parse_approval_file(self, filepath: Path) -> Optional[Dict]:
        """
        Parse approval request markdown file.
        Returns dict with content and metadata.
        """
        try:
            content = filepath.read_text(encoding="utf-8")

            # Extract post content (between ## LinkedIn Post Content and ## To Approve)
            start_marker = "## LinkedIn Post Content"
            end_marker = "## To Approve"

            if start_marker not in content or end_marker not in content:
                log.warning(f"Could not find content markers in {filepath.name}")
                return None

            start = content.index(start_marker) + len(start_marker)
            end = content.index(end_marker)
            post_content = content[start:end].strip()

            # Extract metadata from frontmatter
            metadata = {
                "filepath": filepath,
                "filename": filepath.name,
                "content": post_content,
                "content_length": len(post_content),
            }

            # Parse YAML frontmatter if present
            if "---" in content:
                try:
                    frontmatter_start = content.index("---") + 3
                    frontmatter_end = content.index("---", frontmatter_start)
                    frontmatter = content[frontmatter_start:frontmatter_end]

                    for line in frontmatter.split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            metadata[key.strip()] = value.strip()
                except Exception:
                    pass  # Frontmatter parsing is optional

            return metadata

        except Exception as e:
            log.error(f"Error parsing {filepath.name}: {e}")
            return None

    def process_post(self, metadata: Dict) -> bool:
        """
        Execute a single LinkedIn post.
        Returns True on success, False on failure.
        """
        content = metadata.get("content", "")
        filename = metadata.get("filename", "unknown")

        log.info(f"Processing: {filename}")
        log.info(f"Content length: {len(content)} characters")

        if self.dry_run:
            log.info(f"[DRY RUN] Would post: {content[:100]}...")
            self._log_action("dry_run", metadata)
            return True

        # Check authentication first
        if not self.server.client.is_authenticated():
            log.error("Not authenticated. Run: python linkedin_mcp_server.py --authenticate")
            self._log_action("auth_error", metadata)
            return False

        # Post to LinkedIn
        result = self.server.client.post(content)

        if result.get("success"):
            log.info(f"✓ Posted successfully!")
            log.info(f"  Screenshot: {result.get('screenshot', 'N/A')}")
            log.info(f"  Timestamp: {result.get('timestamp', 'N/A')}")

            self._log_action("posted", metadata, result)

            # Move to Done
            done_path = DONE_DIR / filename
            try:
                metadata["filepath"].rename(done_path)
                log.info(f"  Moved to: {done_path}")
            except Exception as e:
                log.warning(f"Could not move file to Done: {e}")

            return True

        else:
            error_msg = result.get("message", "Unknown error")
            log.error(f"✗ Post failed: {error_msg}")

            self._log_action("error", metadata, {"error": error_msg})
            return False

    def _log_action(self, action_type: str, metadata: Dict, result: Dict = None):
        """Write audit log entry."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": "linkedin_orchestrator",
            "file": metadata.get("filename", "unknown"),
            "content_length": metadata.get("content_length", 0),
        }

        if result:
            log_entry["result"] = result

        log_file = LOGS_DIR / f"linkedin_{datetime.now().strftime('%Y-%m-%d')}.json"

        entries = []
        if log_file.exists():
            try:
                entries = json.loads(log_file.read_text())
            except Exception:
                entries = []

        entries.append(log_entry)
        log_file.write_text(json.dumps(entries, indent=2))

    def process_all_approved(self) -> Dict:
        """
        Process all approved LinkedIn post files.
        Returns summary dict.
        """
        log.info("=" * 55)
        log.info("  LINKEDIN POST ORCHESTRATOR")
        log.info("=" * 55)
        log.info(f"  Approved folder: {APPROVED_DIR}")
        log.info(f"  Dry run: {self.dry_run}")
        log.info("=" * 55)

        approved_files = sorted(APPROVED_DIR.glob("LINKEDIN_POST_*.md"))

        if not approved_files:
            log.info("No approved posts to process.")
            return {"processed": 0, "success": 0, "errors": 0}

        log.info(f"Found {len(approved_files)} approved post(s)")

        for filepath in approved_files:
            metadata = self.parse_approval_file(filepath)

            if not metadata:
                log.warning(f"Skipping {filepath.name} - could not parse")
                self.error_count += 1
                continue

            if self.process_post(metadata):
                self.processed_count += 1
            else:
                self.error_count += 1

            time.sleep(2)  # Rate limiting

        summary = {
            "processed": self.processed_count,
            "success": self.processed_count,
            "errors": self.error_count,
            "total_found": len(approved_files)
        }

        log.info("\n" + "=" * 55)
        log.info("  SUMMARY")
        log.info("=" * 55)
        log.info(f"  Total found    : {len(approved_files)}")
        log.info(f"  Processed      : {self.processed_count}")
        log.info(f"  Errors         : {self.error_count}")
        log.info("=" * 55)

        return summary

    def watch_mode(self, check_interval: int = 60):
        """
        Continuous watch mode - monitors Approved folder.
        """
        log.info(f"Starting watch mode (checking every {check_interval}s)...")
        log.info("Press Ctrl+C to stop.\n")

        try:
            while True:
                result = self.process_all_approved()

                if result["total_found"] > 0:
                    log.info(f"\nSleeping {check_interval}s before next check...\n")

                time.sleep(check_interval)

        except KeyboardInterrupt:
            log.info("\nWatch mode stopped by user.")


# ─────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="LinkedIn Post Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all approved posts
  python linkedin_orchestrator.py

  # Dry run (log only)
  python linkedin_orchestrator.py --dry-run

  # Continuous watch mode
  python linkedin_orchestrator.py --watch --interval 60
        """
    )

    parser.add_argument("--dry-run", action="store_true",
                        help="Log intended actions without posting")

    parser.add_argument("--watch", "-w", action="store_true",
                        help="Continuous watch mode")

    parser.add_argument("--interval", "-i", type=int, default=60,
                        help="Check interval in seconds (default: 60)")

    parser.add_argument("--check-auth", action="store_true",
                        help="Check authentication status and exit")

    args = parser.parse_args()

    orchestrator = LinkedInOrchestrator(dry_run=args.dry_run)

    if args.check_auth:
        is_auth = orchestrator.server.client.is_authenticated()
        print(f"\nLinkedIn Authentication: {'✓ AUTHENTICATED' if is_auth else '✗ NOT AUTHENTICATED'}")
        print(f"Session path: {orchestrator.server.client.session_path}\n")

        if not is_auth:
            print("Run: python scripts/mcp/linkedin_mcp_server.py --authenticate\n")
            sys.exit(1)

    elif args.watch:
        orchestrator.watch_mode(check_interval=args.interval)

    else:
        orchestrator.process_all_approved()


if __name__ == "__main__":
    main()
