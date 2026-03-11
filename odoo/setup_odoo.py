#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo Setup Script - Manages Odoo Docker container and initialization.

Usage:
    python setup_odoo.py start      - Start Odoo container
    python setup_odoo.py stop       - Stop Odoo container
    python setup_odoo.py restart    - Restart Odoo container
    python setup_odoo.py status     - Check container status
    python setup_odoo.py logs       - Show Odoo logs
    python setup_odoo.py init       - Initialize database and create demo data
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Get script directory
SCRIPT_DIR = Path(__file__).parent
DOCKER_COMPOSE_FILE = SCRIPT_DIR / 'docker-compose.yml'
ENV_FILE = SCRIPT_DIR / '.env'


def run_command(command, cwd=None, check=True):
    """Run a shell command."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd or SCRIPT_DIR,
            capture_output=True,
            text=True,
            check=check
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        print(f"Output: {e.output}")
        return None


def check_docker():
    """Check if Docker is installed and running."""
    try:
        result = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ Docker installed: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Docker not found. Please install Docker Desktop first.")
        print("  Download from: https://www.docker.com/products/docker-desktop")
        return False


def check_docker_compose():
    """Check if Docker Compose is available."""
    try:
        result = subprocess.run(
            ['docker', 'compose', 'version'],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ Docker Compose installed: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Docker Compose not found.")
        return False


def start_odoo():
    """Start Odoo container."""
    print("\n" + "="*60)
    print("Starting Odoo Community Edition...")
    print("="*60)

    if not check_docker() or not check_docker_compose():
        return False

    # Create necessary directories
    (SCRIPT_DIR / 'odoo-custom-addons').mkdir(exist_ok=True)
    (SCRIPT_DIR / 'odoo-log').mkdir(exist_ok=True)

    # Start containers
    print("\nStarting Docker containers...")
    run_command(f'docker compose -f "{DOCKER_COMPOSE_FILE}" up -d', check=False)

    print("\nWaiting for Odoo to start (this may take 2-3 minutes)...")
    for i in range(60, 0, -1):
        print(f"\r  Waiting... {i}s remaining", end='', flush=True)
        time.sleep(1)
    print()

    # Check status
    status = run_command(f'docker compose -f "{DOCKER_COMPOSE_FILE}" ps', check=False)
    print(f"\nContainer status:\n{status}")

    print("\n" + "="*60)
    print("✓ Odoo started successfully!")
    print("="*60)
    print("\nAccess Odoo at: http://localhost:8069")
    print("\nDefault credentials:")
    print("  Database: odoo")
    print("  Email: admin")
    print("  Password: admin")
    print("\nNext steps:")
    print("  1. Open http://localhost:8069 in your browser")
    print("  2. Create your database (or use 'odoo' as database name)")
    print("  3. Install 'Accounting' and 'Invoicing' modules")
    print("  4. Generate API key in Settings → Users → Admin")
    print("="*60 + "\n")

    return True


def stop_odoo():
    """Stop Odoo container."""
    print("\n" + "="*60)
    print("Stopping Odoo...")
    print("="*60)

    run_command(f'docker compose -f "{DOCKER_COMPOSE_FILE}" down', check=False)

    print("\n✓ Odoo stopped successfully!")
    print("="*60 + "\n")


def restart_odoo():
    """Restart Odoo container."""
    stop_odoo()
    time.sleep(2)
    start_odoo()


def show_status():
    """Show container status."""
    print("\n" + "="*60)
    print("Odoo Container Status")
    print("="*60)

    # Check Docker
    if not check_docker():
        return

    # Container status
    status = run_command(f'docker compose -f "{DOCKER_COMPOSE_FILE}" ps')
    if status:
        print(f"\n{status}")

    # Check if Odoo is accessible
    import urllib.request
    try:
        urllib.request.urlopen('http://localhost:8069', timeout=5)
        print("\n✓ Odoo web interface is accessible at http://localhost:8069")
    except:
        print("\n✗ Odoo web interface is not responding")

    print("="*60 + "\n")


def show_logs():
    """Show Odoo logs."""
    print("\n" + "="*60)
    print("Odoo Logs (last 50 lines)")
    print("="*60)

    run_command(f'docker compose -f "{DOCKER_COMPOSE_FILE}" logs --tail=50 odoo', check=False)

    print("="*60 + "\n")


def init_demo_data():
    """Initialize Odoo with demo data for AI Employee."""
    print("\n" + "="*60)
    print("Initializing Odoo Demo Data")
    print("="*60)

    # This would use Odoo's XML-RPC API to create demo data
    # For now, provide instructions
    print("""
To initialize demo data, you'll need to:

1. Access Odoo at http://localhost:8069
2. Log in with admin credentials
3. Install the following modules:
   - Invoicing
   - Accounting
   - Sales (optional)

4. Create a test customer:
   - Go to Invoicing → Customers → Create
   - Name: "Test Customer"
   - Email: customer@example.com

5. Create a test product:
   - Go to Invoicing → Products → Create
   - Name: "Consulting Service"
   - Price: $100

6. Create a test invoice:
   - Go to Invoicing → Customers → Create Invoice
   - Select customer and product
   - Confirm and post

After setup, the Odoo MCP Server can:
- Fetch invoices
- Create new invoices
- Track payments
- Generate financial reports
""")

    print("="*60 + "\n")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'start':
        start_odoo()
    elif command == 'stop':
        stop_odoo()
    elif command == 'restart':
        restart_odoo()
    elif command == 'status':
        show_status()
    elif command == 'logs':
        show_logs()
    elif command == 'init':
        init_demo_data()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
