#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File System Watcher - Monitors a drop folder for new files.

This is the simplest watcher for Bronze tier. It watches a designated
"Inbox" or "Drop" folder and creates action files when new files appear.

Use cases:
- Drag-and-drop files for processing
- Manual triggers by creating placeholder files
- Integration with other apps that export to filesystem

Usage:
    python filesystem_watcher.py /path/to/vault /path/to/watch/folder
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from base_watcher import BaseWatcher, create_frontmatter


class DropFolderHandler(FileSystemEventHandler):
    """Handles file system events for the drop folder."""
    
    def __init__(self, needs_action_folder: Path):
        """
        Initialize the handler.
        
        Args:
            needs_action_folder: Path to the Needs_Action folder
        """
        super().__init__()
        self.needs_action = needs_action_folder
        self.processed_files = set()
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        source = Path(event.src_path)
        
        # Skip hidden files and temporary files
        if source.name.startswith('.') or source.name.endswith('.tmp'):
            return
        
        # Skip if already processed
        if str(source) in self.processed_files:
            return
        
        self.processed_files.add(str(source))
        
        # Create action file
        self.create_action_file(source)
    
    def create_action_file(self, source: Path):
        """Create an action file for the dropped file."""
        # Copy file to Needs_Action folder
        dest = self.needs_action / f'FILE_{source.name}'
        
        try:
            shutil.copy2(source, dest)
        except Exception as e:
            print(f"Error copying file: {e}")
            return
        
        # Create metadata file
        meta_path = dest.with_suffix('.md')
        size = source.stat().st_size
        
        content = f"""{create_frontmatter(
            type='file_drop',
            original_name=source.name,
            size=size,
            received=datetime.now(),
            status='pending'
        )}

# File Drop for Processing

**Original File:** `{source.name}`

**File Size:** {size:,} bytes

**Received:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Suggested Actions

- [ ] Review file contents
- [ ] Determine required action
- [ ] Process and move to /Done

---

*Created by File System Watcher*
"""
        meta_path.write_text(content, encoding='utf-8')
        print(f"Created action file: {meta_path.name}")


class FileSystemWatcher(BaseWatcher):
    """Watcher that monitors a folder for new files."""
    
    def __init__(self, vault_path: str, watch_folder: str = None, check_interval: int = 5):
        """
        Initialize the file system watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            watch_folder: Path to folder to watch (default: /Inbox in vault)
            check_interval: Check interval (not used with Observer)
        """
        super().__init__(vault_path, check_interval)
        
        # Use /Inbox folder in vault as default watch folder
        self.watch_folder = Path(watch_folder) if watch_folder else self.vault_path / 'Inbox'
        self.watch_folder.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f'Watching folder: {self.watch_folder}')
    
    def check_for_updates(self) -> list:
        """
        Check for files in the watch folder.
        
        This is called by the base class but we use Observer instead,
        so this returns an empty list.
        """
        return []
    
    def create_action_file(self, item) -> Path:
        """Not used with Observer pattern."""
        pass
    
    def run(self):
        """Run the file system observer."""
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Watch folder: {self.watch_folder}')
        
        event_handler = DropFolderHandler(self.needs_action)
        observer = Observer()
        observer.schedule(event_handler, str(self.watch_folder), recursive=False)
        observer.start()
        
        self.logger.info('File System Watcher started. Press Ctrl+C to stop.')
        print(f"Watching: {self.watch_folder}")
        print("Drop files here to trigger AI processing.")
        
        try:
            while observer.is_alive():
                observer.join(timeout=1)
        except KeyboardInterrupt:
            observer.stop()
            self.logger.info(f'{self.__class__.__name__} stopped by user')
        
        observer.join()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python filesystem_watcher.py <vault_path> [watch_folder]")
        print("\nExamples:")
        print("  python filesystem_watcher.py /path/to/vault")
        print("  python filesystem_watcher.py /path/to/vault /path/to/drop/folder")
        sys.exit(1)
    
    vault_path = sys.argv[1]
    watch_folder = sys.argv[2] if len(sys.argv) > 2 else None
    
    watcher = FileSystemWatcher(vault_path, watch_folder)
    watcher.run()


if __name__ == "__main__":
    main()
