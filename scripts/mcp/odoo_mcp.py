#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo MCP Server - Odoo 19+ JSON-RPC API integration.

Provides MCP tools for:
- create_invoice: Create a new customer invoice
- get_invoices: List invoices (with filters)
- get_invoice: Get specific invoice details
- create_customer: Create a new customer
- get_customers: List customers
- create_product: Create a new product/service
- get_products: List products
- register_payment: Register payment for an invoice (requires HITL approval)
- get_account_moves: Get accounting entries
- get_financial_reports: Get financial summaries

Usage:
    python odoo_mcp.py [--port PORT] [--host HOST]
"""

import sys
import json
import logging
import xmlrpc.client
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


class OdooMCPServer:
    """MCP Server for Odoo ERP integration."""

    def __init__(self, host: str = 'localhost', port: int = 8069,
                 db: str = 'odoo', username: str = 'admin',
                 password: str = 'admin', vault_path: str = '.'):
        """
        Initialize Odoo MCP Server.

        Args:
            host: Odoo server host
            port: Odoo server port
            db: Database name
            username: Odoo username (email)
            password: Odoo password or API key
            vault_path: Path to Obsidian vault for HITL workflow
        """
        self.host = host
        self.port = port
        self.db = db
        self.username = username
        self.password = password
        self.vault_path = Path(vault_path)

        # Odoo XML-RPC URLs
        self.common = xmlrpc.client.ServerProxy(
            f'http://{host}:{port}/xmlrpc/2/common'
        )
        self.models = xmlrpc.client.ServerProxy(
            f'http://{host}:{port}/xmlrpc/2/object'
        )

        # HITL folders
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.logs = self.vault_path / 'Logs'
        self.accounting = self.vault_path / 'Accounting'

        for folder in [self.pending_approval, self.approved, self.logs, self.accounting]:
            folder.mkdir(parents=True, exist_ok=True)

        self.uid = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def authenticate(self) -> bool:
        """Authenticate with Odoo."""
        try:
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
            if self.uid:
                self.logger.info(f'Authenticated with Odoo as user ID: {self.uid}')
                return True
            else:
                self.logger.error('Authentication failed - invalid credentials')
                return False
        except Exception as e:
            self.logger.error(f'Authentication error: {e}')
            return False

    def _check_auth(self) -> bool:
        """Check if authenticated, attempt auth if not."""
        if not self.uid:
            return self.authenticate()
        return True

    def execute(self, model: str, method: str, *args, **kwargs):
        """Execute a method on an Odoo model."""
        if not self._check_auth():
            raise Exception("Not authenticated with Odoo")

        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, method, args, kwargs
            )
        except Exception as e:
            self.logger.error(f'Odoo execute error ({model}.{method}): {e}')
            raise

    def execute_kw(self, model: str, method: str, args: list = None, kwargs: dict = None):
        """Execute with keyword arguments."""
        if not self._check_auth():
            raise Exception("Not authenticated with Odoo")

        args = args or []
        kwargs = kwargs or {}

        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, method, args, kwargs
            )
        except Exception as e:
            self.logger.error(f'Odoo execute_kw error ({model}.{method}): {e}')
            raise

    # ==================== Invoice Operations ====================

    def create_invoice(self, partner_id: int, invoice_type: str = 'out_invoice',
                       lines: List[Dict] = None, invoice_date: str = None,
                       narrative: str = None) -> Dict:
        """
        Create a new customer invoice.

        Args:
            partner_id: Customer ID
            invoice_type: 'out_invoice' (customer) or 'in_invoice' (vendor)
            lines: List of invoice line dicts with product_id, quantity, price_unit
            invoice_date: Invoice date (YYYY-MM-DD)
            narrative: Invoice narrative/description

        Returns:
            Dict with invoice ID and status
        """
        try:
            # Prepare invoice values
            invoice_vals = {
                'move_type': invoice_type,
                'partner_id': partner_id,
                'invoice_date': invoice_date or datetime.now().strftime('%Y-%m-%d'),
                'invoice_origin': 'AI Employee Auto-Generated',
                'narrative': narrative or '',
            }

            # Create invoice
            invoice_id = self.execute('account.move', 'create', invoice_vals)

            # Add invoice lines if provided
            if lines:
                line_vals = []
                for line in lines:
                    line_vals.append((0, 0, {
                        'product_id': line.get('product_id'),
                        'quantity': line.get('quantity', 1),
                        'price_unit': line.get('price_unit', 0),
                        'name': line.get('name', 'Service'),
                    }))

                if line_vals:
                    self.execute('account.move', 'write', [invoice_id], {
                        'invoice_line_ids': line_vals
                    })

            # Compute invoice totals
            self.execute('account.move', 'action_post', [invoice_id])

            self.logger.info(f'Created invoice ID: {invoice_id}')

            return {
                'status': 'success',
                'invoice_id': invoice_id,
                'message': f'Invoice {invoice_id} created and posted'
            }

        except Exception as e:
            self.logger.error(f'Failed to create invoice: {e}')
            return {'error': str(e)}

    def get_invoices(self, limit: int = 10, offset: int = 0,
                     partner_id: int = None, state: str = None,
                     date_from: str = None, date_to: str = None) -> Dict:
        """Get list of invoices with optional filters."""
        try:
            domain = []

            if partner_id:
                domain.append(('partner_id', '=', partner_id))
            if state:
                domain.append(('state', '=', state))
            if date_from:
                domain.append(('invoice_date', '>=', date_from))
            if date_to:
                domain.append(('invoice_date', '<=', date_to))

            invoice_ids = self.execute_kw(
                'account.move',
                'search',
                [domain],
                {'limit': limit, 'offset': offset, 'order': 'invoice_date desc'}
            )

            if not invoice_ids:
                return {'status': 'success', 'count': 0, 'invoices': []}

            # Read invoice details
            invoices = self.execute_kw(
                'account.move',
                'read',
                [invoice_ids],
                {
                    'fields': [
                        'id', 'name', 'partner_id', 'amount_total',
                        'amount_residual', 'state', 'invoice_date',
                        'invoice_date_due', 'move_type'
                    ]
                }
            )

            # Format partner_id (it's a tuple [id, name])
            for inv in invoices:
                if isinstance(inv.get('partner_id'), (list, tuple)):
                    inv['partner_name'] = inv['partner_id'][1]
                    inv['partner_id'] = inv['partner_id'][0]

            return {
                'status': 'success',
                'count': len(invoices),
                'invoices': invoices
            }

        except Exception as e:
            self.logger.error(f'Failed to get invoices: {e}')
            return {'error': str(e)}

    def get_invoice(self, invoice_id: int) -> Dict:
        """Get specific invoice details."""
        try:
            invoices = self.execute_kw(
                'account.move',
                'read',
                [[invoice_id]],
                {
                    'fields': [
                        'id', 'name', 'partner_id', 'amount_total',
                        'amount_residual', 'state', 'invoice_date',
                        'invoice_date_due', 'move_type', 'narrative',
                        'invoice_line_ids', 'payment_state'
                    ]
                }
            )

            if not invoices:
                return {'error': f'Invoice {invoice_id} not found'}

            invoice = invoices[0]

            # Format partner_id
            if isinstance(invoice.get('partner_id'), (list, tuple)):
                invoice['partner_name'] = invoice['partner_id'][1]
                invoice['partner_id'] = invoice['partner_id'][0]

            # Get invoice lines
            if invoice.get('invoice_line_ids'):
                lines = self.execute_kw(
                    'account.move.line',
                    'read',
                    [invoice['invoice_line_ids']],
                    {
                        'fields': ['product_id', 'quantity', 'price_unit',
                                   'name', 'price_subtotal']
                    }
                )
                invoice['lines'] = lines

            return {
                'status': 'success',
                'invoice': invoice
            }

        except Exception as e:
            self.logger.error(f'Failed to get invoice: {e}')
            return {'error': str(e)}

    # ==================== Customer Operations ====================

    def create_customer(self, name: str, email: str = None, phone: str = None,
                        street: str = None, city: str = None,
                        country_id: int = None) -> Dict:
        """Create a new customer."""
        try:
            customer_vals = {
                'name': name,
                'email': email,
                'phone': phone,
                'street': street,
                'city': city,
                'country_id': country_id,
                'company_type': 'person' if email else 'company',
            }

            customer_id = self.execute('res.partner', 'create', customer_vals)

            self.logger.info(f'Created customer ID: {customer_id}')

            return {
                'status': 'success',
                'customer_id': customer_id,
                'message': f'Customer "{name}" created'
            }

        except Exception as e:
            self.logger.error(f'Failed to create customer: {e}')
            return {'error': str(e)}

    def get_customers(self, limit: int = 50, search: str = None) -> Dict:
        """Get list of customers."""
        try:
            domain = []
            if search:
                domain.append(('name', 'ilike', search))

            customer_ids = self.execute_kw(
                'res.partner',
                'search',
                [domain],
                {'limit': limit}
            )

            if not customer_ids:
                return {'status': 'success', 'count': 0, 'customers': []}

            customers = self.execute_kw(
                'res.partner',
                'read',
                [customer_ids],
                {
                    'fields': ['id', 'name', 'email', 'phone',
                               'street', 'city', 'country_id']
                }
            )

            return {
                'status': 'success',
                'count': len(customers),
                'customers': customers
            }

        except Exception as e:
            self.logger.error(f'Failed to get customers: {e}')
            return {'error': str(e)}

    # ==================== Product Operations ====================

    def create_product(self, name: str, list_price: float = 0.0,
                       product_type: str = 'service',
                       uom_name: str = 'Units') -> Dict:
        """Create a new product/service."""
        try:
            product_vals = {
                'name': name,
                'list_price': list_price,
                'type': 'product' if product_type == 'storable' else 'service',
                'uom_name': uom_name,
                'detailed_type': 'product_product' if product_type == 'storable' else 'service',
            }

            product_id = self.execute('product.template', 'create', product_vals)

            self.logger.info(f'Created product ID: {product_id}')

            return {
                'status': 'success',
                'product_id': product_id,
                'message': f'Product "{name}" created'
            }

        except Exception as e:
            self.logger.error(f'Failed to create product: {e}')
            return {'error': str(e)}

    def get_products(self, limit: int = 50, search: str = None) -> Dict:
        """Get list of products."""
        try:
            domain = []
            if search:
                domain.append(('name', 'ilike', search))

            product_ids = self.execute_kw(
                'product.template',
                'search',
                [domain],
                {'limit': limit}
            )

            if not product_ids:
                return {'status': 'success', 'count': 0, 'products': []}

            products = self.execute_kw(
                'product.template',
                'read',
                [product_ids],
                {
                    'fields': ['id', 'name', 'list_price', 'type', 'uom_name']
                }
            )

            return {
                'status': 'success',
                'count': len(products),
                'products': products
            }

        except Exception as e:
            self.logger.error(f'Failed to get products: {e}')
            return {'error': str(e)}

    # ==================== Payment Operations ====================

    def register_payment(self, invoice_id: int, amount: float,
                         payment_date: str = None,
                         payment_method: str = 'manual') -> Dict:
        """
        Register payment for an invoice.

        For sensitive actions, creates HITL approval file first.
        """
        try:
            # Get invoice details
            invoice_data = self.get_invoice(invoice_id)
            if 'error' in invoice_data:
                return invoice_data

            invoice = invoice_data['invoice']

            # Create approval file for HITL
            approval_file = self._create_payment_approval_request(
                invoice_id=invoice_id,
                invoice_name=invoice.get('name', 'Unknown'),
                partner_name=invoice.get('partner_name', 'Unknown'),
                amount=amount,
                payment_date=payment_date,
                payment_method=payment_method
            )

            return {
                'status': 'pending_approval',
                'approval_file': str(approval_file),
                'message': f'Approval file created: {approval_file.name}'
            }

        except Exception as e:
            self.logger.error(f'Failed to register payment: {e}')
            return {'error': str(e)}

    def _create_payment_approval_request(self, invoice_id: int,
                                          invoice_name: str,
                                          partner_name: str,
                                          amount: float,
                                          payment_date: str = None,
                                          payment_method: str = 'manual') -> Path:
        """Create HITL approval request file for payment."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = self.pending_approval / f"PAYMENT_{invoice_name}_{timestamp}.md"

        content = f"""---
type: approval_request
action: register_payment
invoice_id: {invoice_id}
invoice_name: {invoice_name}
partner_name: {partner_name}
amount: {amount}
payment_date: {payment_date or datetime.now().strftime('%Y-%m-%d')}
payment_method: {payment_method}
created: {datetime.now().isoformat()}
status: pending
---

# Payment Approval Request

**Invoice:** {invoice_name}

**Customer:** {partner_name}

**Amount:** ${amount:,.2f}

**Payment Date:** {payment_date or datetime.now().strftime('%Y-%m-%d')}

**Payment Method:** {payment_method}

---

## To Approve
Move this file to /Approved folder.

## To Reject
Move this file to /Rejected folder.

---

*Created by Odoo MCP Server*
"""
        filepath.write_text(content, encoding='utf-8')
        self.logger.info(f'Created payment approval request: {filepath.name}')
        return filepath

    # ==================== Accounting Operations ====================

    def get_account_moves(self, limit: int = 50, account_code: str = None,
                          date_from: str = None, date_to: str = None) -> Dict:
        """Get accounting entries (journal items)."""
        try:
            domain = []

            if account_code:
                domain.append(('account_id.code', '=', account_code))
            if date_from:
                domain.append(('date', '>=', date_from))
            if date_to:
                domain.append(('date', '<=', date_to))

            move_line_ids = self.execute_kw(
                'account.move.line',
                'search',
                [domain],
                {'limit': limit, 'order': 'date desc'}
            )

            if not move_line_ids:
                return {'status': 'success', 'count': 0, 'moves': []}

            moves = self.execute_kw(
                'account.move.line',
                'read',
                [move_line_ids],
                {
                    'fields': [
                        'id', 'date', 'name', 'account_id', 'debit',
                        'credit', 'balance', 'move_id', 'partner_id'
                    ]
                }
            )

            # Format account_id and partner_id
            for move in moves:
                if isinstance(move.get('account_id'), (list, tuple)):
                    move['account_name'] = move['account_id'][1]
                    move['account_code'] = move['account_id'][0]
                    move['account_id'] = move['account_id'][0]
                if isinstance(move.get('partner_id'), (list, tuple)):
                    move['partner_name'] = move['partner_id'][1]
                    move['partner_id'] = move['partner_id'][0]
                if isinstance(move.get('move_id'), (list, tuple)):
                    move['move_name'] = move['move_id'][1]
                    move['move_id'] = move['move_id'][0]

            return {
                'status': 'success',
                'count': len(moves),
                'moves': moves
            }

        except Exception as e:
            self.logger.error(f'Failed to get account moves: {e}')
            return {'error': str(e)}

    def get_financial_reports(self, report_type: str = 'summary') -> Dict:
        """Get financial summary reports."""
        try:
            # Get total receivables
            receivable_domain = [('account_type', '=', 'asset_receivable')]
            receivable_accounts = self.execute_kw(
                'account.account',
                'search',
                [receivable_domain]
            )

            # Get total payables
            payable_domain = [('account_type', '=', 'liability_payable')]
            payable_accounts = self.execute_kw(
                'account.account',
                'search',
                [payable_domain]
            )

            # Calculate totals
            total_receivable = 0
            total_payable = 0

            if receivable_accounts:
                receivable_moves = self.execute_kw(
                    'account.move.line',
                    'search',
                    [[('account_id', 'in', receivable_accounts)]]
                )
                if receivable_moves:
                    receivable_lines = self.execute_kw(
                        'account.move.line',
                        'read',
                        [receivable_moves],
                        {'fields': ['balance']}
                    )
                    total_receivable = sum(line.get('balance', 0) for line in receivable_lines)

            if payable_accounts:
                payable_moves = self.execute_kw(
                    'account.move.line',
                    'search',
                    [[('account_id', 'in', payable_accounts)]]
                )
                if payable_moves:
                    payable_lines = self.execute_kw(
                        'account.move.line',
                        'read',
                        [payable_moves],
                        {'fields': ['balance']}
                    )
                    total_payable = sum(line.get('balance', 0) for line in payable_lines)

            # Get invoice statistics
            today = datetime.now().strftime('%Y-%m-%d')
            month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

            invoices_total = self.execute_kw(
                'account.move',
                'search',
                    [[('move_type', 'in', ['out_invoice', 'out_refund']), ('state', '=', 'posted')]]
            )

            month_invoices = self.execute_kw(
                'account.move',
                'search',
                [[
                    ('move_type', 'in', ['out_invoice', 'out_refund']),
                    ('state', '=', 'posted'),
                    ('invoice_date', '>=', month_ago)
                ]]
            )

            # Calculate revenue
            revenue = 0
            if invoices_total:
                invoices_data = self.execute_kw(
                    'account.move',
                    'read',
                    [invoices_total],
                    {'fields': ['amount_total']}
                )
                revenue = sum(inv.get('amount_total', 0) for inv in invoices_data)

            month_revenue = 0
            if month_invoices:
                month_invoices_data = self.execute_kw(
                    'account.move',
                    'read',
                    [month_invoices],
                    {'fields': ['amount_total']}
                )
                month_revenue = sum(inv.get('amount_total', 0) for inv in month_invoices_data)

            return {
                'status': 'success',
                'report': {
                    'total_receivable': total_receivable,
                    'total_payable': total_payable,
                    'total_revenue': revenue,
                    'monthly_revenue': month_revenue,
                    'total_invoices': len(invoices_total),
                    'month_invoices': len(month_invoices),
                    'generated_at': datetime.now().isoformat()
                }
            }

        except Exception as e:
            self.logger.error(f'Failed to get financial reports: {e}')
            return {'error': str(e)}

    # ==================== Logging ====================

    def log_action(self, action_type: str, details: Dict, status: str = 'info'):
        """Log an action to the accounting log."""
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs / f'odoo_{today}.md'

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        entry = f'[{timestamp}] [{status.upper()}] {action_type}: {json.dumps(details)}'

        if log_file.exists():
            content = log_file.read_text(encoding='utf-8')
            content = content.rstrip() + '\n' + entry + '\n'
        else:
            content = f"# Odoo Actions Log - {today}\n\n{entry}\n"

        log_file.write_text(content, encoding='utf-8')


def create_mcp_server_tools(odoo_server: OdooMCPServer) -> List[Tool]:
    """Create MCP tool definitions."""
    return [
        Tool(
            name="create_invoice",
            description="Create a new customer invoice in Odoo",
            inputSchema={
                "type": "object",
                "properties": {
                    "partner_id": {"type": "integer", "description": "Customer ID"},
                    "invoice_type": {"type": "string", "description": "Invoice type (out_invoice or in_invoice)", "default": "out_invoice"},
                    "lines": {"type": "array", "items": {"type": "object", "properties": {"product_id": {"type": "integer"}, "quantity": {"type": "number"}, "price_unit": {"type": "number"}, "name": {"type": "string"}}}, "description": "Invoice lines"},
                    "invoice_date": {"type": "string", "description": "Invoice date (YYYY-MM-DD)"},
                    "narrative": {"type": "string", "description": "Invoice narrative"}
                },
                "required": ["partner_id"]
            }
        ),
        Tool(
            name="get_invoices",
            description="List invoices from Odoo with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max results", "default": 10},
                    "offset": {"type": "integer", "description": "Offset", "default": 0},
                    "partner_id": {"type": "integer", "description": "Filter by customer ID"},
                    "state": {"type": "string", "description": "Filter by state (draft, posted, cancel)"},
                    "date_from": {"type": "string", "description": "Filter from date (YYYY-MM-DD)"},
                    "date_to": {"type": "string", "description": "Filter to date (YYYY-MM-DD)"}
                }
            }
        ),
        Tool(
            name="get_invoice",
            description="Get specific invoice details by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "integer", "description": "Invoice ID"}
                },
                "required": ["invoice_id"]
            }
        ),
        Tool(
            name="create_customer",
            description="Create a new customer in Odoo",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Customer name"},
                    "email": {"type": "string", "description": "Email address"},
                    "phone": {"type": "string", "description": "Phone number"},
                    "street": {"type": "string", "description": "Street address"},
                    "city": {"type": "string", "description": "City"},
                    "country_id": {"type": "integer", "description": "Country ID"}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="get_customers",
            description="List customers from Odoo",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max results", "default": 50},
                    "search": {"type": "string", "description": "Search term"}
                }
            }
        ),
        Tool(
            name="create_product",
            description="Create a new product/service in Odoo",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Product name"},
                    "list_price": {"type": "number", "description": "Sale price", "default": 0},
                    "product_type": {"type": "string", "description": "Type (service or storable)", "default": "service"},
                    "uom_name": {"type": "string", "description": "Unit of measure", "default": "Units"}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="get_products",
            description="List products from Odoo",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max results", "default": 50},
                    "search": {"type": "string", "description": "Search term"}
                }
            }
        ),
        Tool(
            name="register_payment",
            description="Register payment for an invoice (requires HITL approval)",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "integer", "description": "Invoice ID"},
                    "amount": {"type": "number", "description": "Payment amount"},
                    "payment_date": {"type": "string", "description": "Payment date (YYYY-MM-DD)"},
                    "payment_method": {"type": "string", "description": "Payment method", "default": "manual"}
                },
                "required": ["invoice_id", "amount"]
            }
        ),
        Tool(
            name="get_account_moves",
            description="Get accounting journal entries",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max results", "default": 50},
                    "account_code": {"type": "string", "description": "Filter by account code"},
                    "date_from": {"type": "string", "description": "Filter from date (YYYY-MM-DD)"},
                    "date_to": {"type": "string", "description": "Filter to date (YYYY-MM-DD)"}
                }
            }
        ),
        Tool(
            name="get_financial_reports",
            description="Get financial summary reports",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_type": {"type": "string", "description": "Report type (summary)", "default": "summary"}
                }
            }
        )
    ]


async def run_mcp_server(odoo_server: OdooMCPServer):
    """Run MCP server using stdio transport."""
    if not MCP_AVAILABLE:
        print("MCP library not available")
        return

    server = Server("odoo-mcp")
    tools = create_mcp_server_tools(odoo_server)

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict) -> List[TextContent]:
        try:
            if name == "create_invoice":
                result = odoo_server.create_invoice(
                    partner_id=arguments.get('partner_id'),
                    invoice_type=arguments.get('invoice_type', 'out_invoice'),
                    lines=arguments.get('lines'),
                    invoice_date=arguments.get('invoice_date'),
                    narrative=arguments.get('narrative')
                )
            elif name == "get_invoices":
                result = odoo_server.get_invoices(
                    limit=arguments.get('limit', 10),
                    offset=arguments.get('offset', 0),
                    partner_id=arguments.get('partner_id'),
                    state=arguments.get('state'),
                    date_from=arguments.get('date_from'),
                    date_to=arguments.get('date_to')
                )
            elif name == "get_invoice":
                result = odoo_server.get_invoice(
                    invoice_id=arguments.get('invoice_id')
                )
            elif name == "create_customer":
                result = odoo_server.create_customer(
                    name=arguments.get('name'),
                    email=arguments.get('email'),
                    phone=arguments.get('phone'),
                    street=arguments.get('street'),
                    city=arguments.get('city'),
                    country_id=arguments.get('country_id')
                )
            elif name == "get_customers":
                result = odoo_server.get_customers(
                    limit=arguments.get('limit', 50),
                    search=arguments.get('search')
                )
            elif name == "create_product":
                result = odoo_server.create_product(
                    name=arguments.get('name'),
                    list_price=arguments.get('list_price', 0),
                    product_type=arguments.get('product_type', 'service'),
                    uom_name=arguments.get('uom_name', 'Units')
                )
            elif name == "get_products":
                result = odoo_server.get_products(
                    limit=arguments.get('limit', 50),
                    search=arguments.get('search')
                )
            elif name == "register_payment":
                result = odoo_server.register_payment(
                    invoice_id=arguments.get('invoice_id'),
                    amount=arguments.get('amount'),
                    payment_date=arguments.get('payment_date'),
                    payment_method=arguments.get('payment_method', 'manual')
                )
            elif name == "get_account_moves":
                result = odoo_server.get_account_moves(
                    limit=arguments.get('limit', 50),
                    account_code=arguments.get('account_code'),
                    date_from=arguments.get('date_from'),
                    date_to=arguments.get('date_to')
                )
            elif name == "get_financial_reports":
                result = odoo_server.get_financial_reports(
                    report_type=arguments.get('report_type', 'summary')
                )
            else:
                result = {'error': f'Unknown tool: {name}'}

            # Log action
            odoo_server.log_action(name, arguments)

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            error_result = {'error': str(e)}
            odoo_server.log_action(name, arguments, 'error')
            return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Main entry point."""
    import argparse

    # Load environment variables
    load_dotenv()

    parser = argparse.ArgumentParser(description='Odoo MCP Server')
    parser.add_argument('--host', type=str, default=os.getenv('ODOO_HOST', 'localhost'), help='Odoo host')
    parser.add_argument('--port', type=int, default=int(os.getenv('ODOO_PORT', '8069')), help='Odoo port')
    parser.add_argument('--db', type=str, default=os.getenv('ODOO_DB', 'odoo'), help='Database name')
    parser.add_argument('--username', type=str, default=os.getenv('ODOO_USERNAME', 'admin'), help='Odoo username')
    parser.add_argument('--password', type=str, default=os.getenv('ODOO_PASSWORD', 'admin'), help='Odoo password')
    parser.add_argument('--vault', type=str, default='.', help='Path to vault')
    parser.add_argument('--authenticate', action='store_true', help='Test authentication only')

    args = parser.parse_args()

    odoo_server = OdooMCPServer(
        host=args.host,
        port=args.port,
        db=args.db,
        username=args.username,
        password=args.password,
        vault_path=args.vault
    )

    if args.authenticate:
        print("Testing Odoo authentication...")
        if odoo_server.authenticate():
            print('✓ Authentication successful!')
            sys.exit(0)
        else:
            print('✗ Authentication failed!')
            sys.exit(1)

    if not MCP_AVAILABLE:
        print('MCP library not installed.')
        print('Install: pip install mcp')
        sys.exit(1)

    import asyncio
    print(f'Starting Odoo MCP Server...')
    print(f'Connecting to {args.host}:{args.port} (database: {args.db})')
    asyncio.run(run_mcp_server(odoo_server))


if __name__ == "__main__":
    main()
