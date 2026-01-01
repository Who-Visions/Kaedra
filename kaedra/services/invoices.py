"""
KAEDRA v0.0.6 - Invoice Service
Unified invoice management for Stripe and Square.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger("kaedra.services.invoices")


# ══════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ══════════════════════════════════════════════════════════════════════════════

class Provider(Enum):
    STRIPE = "stripe"
    SQUARE = "square"


class InvoiceStatus(Enum):
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


@dataclass
class Customer:
    """Unified customer representation."""
    id: str
    name: str
    email: Optional[str] = None
    provider: str = "stripe"
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InvoiceItem:
    """Line item on an invoice."""
    description: str
    amount: float  # In dollars
    quantity: int = 1
    
    @property
    def total(self) -> float:
        return self.amount * self.quantity


@dataclass
class Invoice:
    """Unified invoice representation."""
    id: str
    provider: str
    customer_name: str
    customer_email: Optional[str]
    status: str
    amount_due: float  # In dollars
    amount_paid: float
    currency: str
    created_at: datetime
    due_date: Optional[datetime] = None
    items: List[InvoiceItem] = field(default_factory=list)
    url: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_paid(self) -> bool:
        return self.status == "paid"
    
    @property
    def is_overdue(self) -> bool:
        if self.due_date and not self.is_paid:
            return datetime.now() > self.due_date
        return False
    
    def to_markdown(self) -> str:
        """Generate a clean Markdown representation of the invoice."""
        lines = []
        lines.append(f"# Invoice {self.id}")
        lines.append(f"**Date:** {self.created_at.strftime('%Y-%m-%d')}")
        if self.due_date:
            lines.append(f"**Due:** {self.due_date.strftime('%Y-%m-%d')}")
        lines.append(f"**Status:** {self.status.upper()}")
        
        lines.append("\n---")
        
        lines.append(f"\n**Bill To:**")
        lines.append(f"{self.customer_name}")
        if self.customer_email:
            lines.append(f"{self.customer_email}")
            
        lines.append("\n## Items")
        lines.append("| Description | Qty | Price | Total |")
        lines.append("| :--- | :---: | :---: | :---: |")
        
        for item in self.items:
            total = item.amount * item.quantity
            lines.append(f"| {item.description} | {item.quantity} | ${item.amount:.2f} | ${total:.2f} |")
            
        lines.append("\n---")
        lines.append(f"**Total Due: ${self.amount_due:.2f}**")
        lines.append(f"**Amount Paid: ${self.amount_paid:.2f}**")
        
        if self.url:
            lines.append(f"\n[View Online Invoice]({self.url})")
            
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# STRIPE INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════

class StripeProvider:
    """Stripe invoice operations."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._stripe = None
    
    @property
    def stripe(self):
        if self._stripe is None:
            try:
                import stripe
                stripe.api_key = self.api_key
                self._stripe = stripe
            except ImportError:
                raise ImportError("stripe package not installed. Run: pip install stripe")
        return self._stripe
    
    def list_invoices(self, status: str = None, limit: int = 25) -> List[Invoice]:
        """List Stripe invoices."""
        params = {"limit": limit}
        if status:
            params["status"] = status
        
        try:
            result = self.stripe.Invoice.list(**params)
            return [self._parse_invoice(inv) for inv in result.data]
        except Exception as e:
            logger.error(f"Stripe list_invoices error: {e}")
            raise
    
    def get_invoice(self, invoice_id: str) -> Invoice:
        """Get single Stripe invoice."""
        try:
            inv = self.stripe.Invoice.retrieve(invoice_id)
            return self._parse_invoice(inv)
        except Exception as e:
            logger.error(f"Stripe get_invoice error: {e}")
            raise
    
    def create_invoice(self, customer_id: str, items: List[Dict[str, Any]], 
                       auto_send: bool = False) -> Invoice:
        """Create a Stripe invoice."""
        try:
            # Create invoice
            inv = self.stripe.Invoice.create(
                customer=customer_id,
                auto_advance=auto_send,
            )
            
            # Add line items
            for item in items:
                self.stripe.InvoiceItem.create(
                    customer=customer_id,
                    invoice=inv.id,
                    description=item.get("description", "Service"),
                    amount=int(item.get("amount", 0) * 100),  # Convert to cents
                    currency=item.get("currency", "usd"),
                )
            
            # Refresh invoice
            inv = self.stripe.Invoice.retrieve(inv.id)
            return self._parse_invoice(inv)
        except Exception as e:
            logger.error(f"Stripe create_invoice error: {e}")
            raise
    
    def send_invoice(self, invoice_id: str) -> Invoice:
        """Finalize and send a Stripe invoice."""
        try:
            inv = self.stripe.Invoice.finalize_invoice(invoice_id)
            inv = self.stripe.Invoice.send_invoice(invoice_id)
            return self._parse_invoice(inv)
        except Exception as e:
            logger.error(f"Stripe send_invoice error: {e}")
            raise
    
    def get_revenue(self, days: int = 30) -> Dict[str, Any]:
        """Get revenue summary for period."""
        try:
            since = datetime.now() - timedelta(days=days)
            since_ts = int(since.timestamp())
            
            invoices = self.stripe.Invoice.list(
                status="paid",
                created={"gte": since_ts},
                limit=100
            )
            
            total = sum(inv.amount_paid for inv in invoices.data) / 100
            count = len(invoices.data)
            
            return {
                "provider": "stripe",
                "period_days": days,
                "total_revenue": total,
                "invoice_count": count,
                "currency": "usd"
            }
        except Exception as e:
            logger.error(f"Stripe get_revenue error: {e}")
            raise
    
    def _parse_invoice(self, inv) -> Invoice:
        """Convert Stripe invoice to unified format."""
        # Get customer info
        customer_name = "Unknown"
        customer_email = None
        if hasattr(inv, 'customer') and inv.customer:
            try:
                cust = self.stripe.Customer.retrieve(inv.customer)
                customer_name = cust.name or cust.email or "Unknown"
                customer_email = cust.email
            except:
                pass
        
        # Parse items
        items = []
        if hasattr(inv, 'lines') and inv.lines:
            for line in inv.lines.data:
                items.append(InvoiceItem(
                    description=line.description or "Item",
                    amount=line.amount / 100,
                    quantity=line.quantity or 1
                ))
        
        return Invoice(
            id=inv.id,
            provider="stripe",
            customer_name=customer_name,
            customer_email=customer_email,
            status=inv.status or "draft",
            amount_due=inv.amount_due / 100,
            amount_paid=inv.amount_paid / 100,
            currency=inv.currency or "usd",
            created_at=datetime.fromtimestamp(inv.created),
            due_date=datetime.fromtimestamp(inv.due_date) if inv.due_date else None,
            items=items,
            url=inv.hosted_invoice_url,
            raw_data=dict(inv)
        )


# ══════════════════════════════════════════════════════════════════════════════
# SQUARE INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════

class SquareProvider:
    """Square invoice operations."""
    
    def __init__(self, access_token: str, environment: str = "sandbox"):
        self.access_token = access_token
        self.environment = environment
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            try:
                # Square SDK v43+ uses new import pattern
                from square import Square
                self._client = Square(token=self.access_token)
            except ImportError:
                try:
                    # Fallback only for older SDK versions
                    from square.client import Client
                    self._client = Client(
                        access_token=self.access_token,
                        environment=self.environment
                    )
                except ImportError:
                    raise ImportError("square package not installed. Run: pip install squareup")
        return self._client
    
    def _is_new_sdk(self) -> bool:
        """Check if using new Square SDK (v43+)."""
        return hasattr(self.client, 'locations') and not hasattr(self.client.locations, 'list_locations')
    
    def list_invoices(self, status: str = None, limit: int = 25) -> List[Invoice]:
        """List Square invoices."""
        try:
            # Get location first - v43+ SDK uses .list() which returns SyncPager
            locations = []
            try:
                locations_result = self.client.locations.list()
                # v43+ returns SyncPager or object with .locations attribute
                if hasattr(locations_result, 'locations'):
                    locations = locations_result.locations or []
                else:
                    # Might be a pager, iterate it
                    locations = list(locations_result)
            except Exception:
                # Fallback for older SDK
                try:
                    locations_result = self.client.locations.list_locations()
                    if locations_result.is_success():
                        locations = locations_result.body.get("locations", [])
                except:
                    pass
            
            if not locations:
                return []
            
            location_id = locations[0].id if hasattr(locations[0], 'id') else locations[0].get("id")
            
            # Get invoices - v43+ SDK returns SyncPager
            invoices = []
            try:
                result = self.client.invoices.list(location_id=location_id)
                # Could be a pager or object with .invoices
                if hasattr(result, '__iter__') and not hasattr(result, 'invoices'):
                    # It's a pager, iterate it
                    raw_invoices = list(result)
                else:
                    # It has .invoices attribute
                    raw_invoices = result.invoices or []
                
                # Convert to dicts for compatibility
                for inv in raw_invoices:
                    if hasattr(inv, 'model_dump'):
                        invoices.append(inv.model_dump())
                    elif hasattr(inv, '__dict__'):
                        invoices.append(vars(inv))
                    else:
                        invoices.append(inv)
            except Exception:
                # Fallback for older SDK
                try:
                    result = self.client.invoices.list_invoices(
                        location_id=location_id,
                        limit=limit
                    )
                    if result.is_success():
                        invoices = result.body.get("invoices", [])
                except:
                    pass
            
            # Filter by status if specified
            if status:
                status_map = {
                    "open": ["UNPAID", "SCHEDULED", "PARTIALLY_PAID"],
                    "paid": ["PAID"],
                    "draft": ["DRAFT"],
                    "void": ["CANCELED"]
                }
                target_statuses = status_map.get(status, [status.upper()])
                invoices = [inv for inv in invoices if inv.get("status") in target_statuses]
            
            return [self._parse_invoice(inv) for inv in invoices]
        except Exception as e:
            logger.error(f"Square list_invoices error: {e}")
            raise
    
    def get_invoice(self, invoice_id: str) -> Invoice:
        """Get single Square invoice."""
        try:
            # v43+ SDK uses .get() not .get_invoice()
            try:
                result = self.client.invoices.get(invoice_id=invoice_id)
                invoice_data = result.invoice.model_dump() if hasattr(result.invoice, 'model_dump') else result.invoice
            except AttributeError:
                result = self.client.invoices.get_invoice(invoice_id=invoice_id)
                if not result.is_success():
                    raise Exception(f"Square error: {result.errors}")
                invoice_data = result.body["invoice"]
            
            return self._parse_invoice(invoice_data)
        except Exception as e:
            logger.error(f"Square get_invoice error: {e}")
            raise
    
    def create_invoice(self, customer_id: str, items: List[Dict[str, Any]], 
                       location_id: str = None) -> Invoice:
        """Create a Square invoice."""
        try:
            # Get location if not provided
            if not location_id:
                try:
                    locations_result = self.client.locations.list()
                    locations = locations_result.locations or []
                    location_id = locations[0].id if hasattr(locations[0], 'id') else locations[0]["id"]
                except AttributeError:
                    locations_result = self.client.locations.list_locations()
                    location_id = locations_result.body["locations"][0]["id"]
            
            import uuid
            
            # Build line items
            line_items = []
            for item in items:
                line_items.append({
                    "uid": str(uuid.uuid4()),
                    "name": item.get("description", "Service"),
                    "quantity": str(item.get("quantity", 1)),
                    "base_price_money": {
                        "amount": int(item.get("amount", 0) * 100),
                        "currency": item.get("currency", "USD").upper()
                    }
                })
            
            body = {
                "invoice": {
                    "location_id": location_id,
                    "order_id": None,  # Will create order automatically
                    "primary_recipient": {
                        "customer_id": customer_id
                    },
                    "payment_requests": [{
                        "request_type": "BALANCE",
                        "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                    }],
                    "delivery_method": "EMAIL"
                },
                "idempotency_key": str(uuid.uuid4())
            }
            
            # v43+ SDK uses .create() not .create_invoice()
            try:
                result = self.client.invoices.create(body=body)
                invoice_data = result.invoice.model_dump() if hasattr(result.invoice, 'model_dump') else result.invoice
            except AttributeError:
                result = self.client.invoices.create_invoice(body=body)
                if not result.is_success():
                    raise Exception(f"Square error: {result.errors}")
                invoice_data = result.body["invoice"]
            
            return self._parse_invoice(invoice_data)
        except Exception as e:
            logger.error(f"Square create_invoice error: {e}")
            raise
    
    def send_invoice(self, invoice_id: str) -> Invoice:
        """Publish and send a Square invoice."""
        try:
            import uuid
            
            # First get current version
            try:
                inv_result = self.client.invoices.get(invoice_id=invoice_id)
                version = inv_result.invoice.version if hasattr(inv_result.invoice, 'version') else inv_result.invoice["version"]
            except AttributeError:
                inv_result = self.client.invoices.get_invoice(invoice_id=invoice_id)
                version = inv_result.body["invoice"]["version"]
            
            # v43+ SDK uses .publish() not .publish_invoice()
            try:
                result = self.client.invoices.publish(
                    invoice_id=invoice_id,
                    body={
                        "version": version,
                        "idempotency_key": str(uuid.uuid4())
                    }
                )
                invoice_data = result.invoice.model_dump() if hasattr(result.invoice, 'model_dump') else result.invoice
            except AttributeError:
                result = self.client.invoices.publish_invoice(
                    invoice_id=invoice_id,
                    body={
                        "version": version,
                        "idempotency_key": str(uuid.uuid4())
                    }
                )
                if not result.is_success():
                    raise Exception(f"Square error: {result.errors}")
                invoice_data = result.body["invoice"]
            
            return self._parse_invoice(invoice_data)
        except Exception as e:
            logger.error(f"Square send_invoice error: {e}")
            raise
    
    def get_revenue(self, days: int = 30) -> Dict[str, Any]:
        """Get revenue summary for period."""
        try:
            invoices = self.list_invoices(status="paid", limit=100)
            since = datetime.now() - timedelta(days=days)
            
            # Filter by date
            recent = [inv for inv in invoices if inv.created_at >= since]
            total = sum(inv.amount_paid for inv in recent)
            
            return {
                "provider": "square",
                "period_days": days,
                "total_revenue": total,
                "invoice_count": len(recent),
                "currency": "usd"
            }
        except Exception as e:
            logger.error(f"Square get_revenue error: {e}")
            raise
    
    def _parse_invoice(self, inv: Dict[str, Any]) -> Invoice:
        """Convert Square invoice to unified format."""
        # Status mapping
        status_map = {
            "DRAFT": "draft",
            "UNPAID": "open",
            "SCHEDULED": "open",
            "PARTIALLY_PAID": "open",
            "PAID": "paid",
            "CANCELED": "void"
        }
        
        # Get amounts
        payment_requests = inv.get("payment_requests", [{}])
        amount_money = payment_requests[0].get("computed_amount_money", {}) if payment_requests else {}
        total_money = payment_requests[0].get("total_completed_amount_money", {}) if payment_requests else {}
        
        amount_due = amount_money.get("amount", 0) / 100
        amount_paid = total_money.get("amount", 0) / 100
        
        # Parse due date
        due_date = None
        if payment_requests and payment_requests[0].get("due_date"):
            try:
                due_date = datetime.strptime(payment_requests[0]["due_date"], "%Y-%m-%d")
            except:
                pass
        
        # Get customer name
        customer_name = "Unknown"
        customer_email = None
        primary = inv.get("primary_recipient", {})
        if primary.get("given_name") or primary.get("family_name"):
            customer_name = f"{primary.get('given_name', '')} {primary.get('family_name', '')}".strip()
        if primary.get("email_address"):
            customer_email = primary["email_address"]
        
        return Invoice(
            id=inv["id"],
            provider="square",
            customer_name=customer_name,
            customer_email=customer_email,
            status=status_map.get(inv.get("status", "DRAFT"), "draft"),
            amount_due=amount_due,
            amount_paid=amount_paid,
            currency=amount_money.get("currency", "USD").lower(),
            created_at=datetime.fromisoformat(inv["created_at"].replace("Z", "+00:00")).replace(tzinfo=None),
            due_date=due_date,
            url=inv.get("public_url"),
            raw_data=inv
        )


# ══════════════════════════════════════════════════════════════════════════════
# UNIFIED INVOICE SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class InvoiceService:
    """
    Unified invoice service for Stripe and Square.
    
    Provides a single interface to manage invoices across both providers.
    """
    
    def __init__(
        self,
        stripe_key: str = None,
        square_token: str = None,
        square_environment: str = "sandbox"
    ):
        self.stripe_key = stripe_key or os.getenv("STRIPE_SECRET_KEY", "")
        self.square_token = square_token or os.getenv("SQUARE_ACCESS_TOKEN", "")
        self.square_environment = square_environment or os.getenv("SQUARE_ENVIRONMENT", "sandbox")
        
        self._stripe = None
        self._square = None
    
    @property
    def stripe(self) -> Optional[StripeProvider]:
        if self._stripe is None and self.stripe_key:
            self._stripe = StripeProvider(self.stripe_key)
        return self._stripe
    
    @property
    def square(self) -> Optional[SquareProvider]:
        if self._square is None and self.square_token:
            self._square = SquareProvider(self.square_token, self.square_environment)
        return self._square
    
    def _get_provider(self, provider: str):
        """Get provider instance by name."""
        if provider == "stripe":
            if not self.stripe:
                raise ValueError("Stripe not configured. Set STRIPE_SECRET_KEY.")
            return self.stripe
        elif provider == "square":
            if not self.square:
                raise ValueError("Square not configured. Set SQUARE_ACCESS_TOKEN.")
            return self.square
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def list_invoices(self, provider: str = "stripe", status: str = None, 
                      limit: int = 25) -> List[Invoice]:
        """
        List invoices from a provider.
        
        Args:
            provider: 'stripe', 'square', or 'both'
            status: 'open', 'paid', 'draft', 'void'
            limit: Max results per provider
        """
        if provider == "both":
            results = []
            if self.stripe:
                try:
                    results.extend(self.stripe.list_invoices(status, limit))
                except Exception as e:
                    logger.warning(f"Stripe list failed: {e}")
            if self.square:
                try:
                    results.extend(self.square.list_invoices(status, limit))
                except Exception as e:
                    logger.warning(f"Square list failed: {e}")
            return sorted(results, key=lambda x: x.created_at, reverse=True)
        
        return self._get_provider(provider).list_invoices(status, limit)
    
    def get_invoice(self, provider: str, invoice_id: str) -> Invoice:
        """Get a single invoice by ID."""
        return self._get_provider(provider).get_invoice(invoice_id)
    
    def create_invoice(self, provider: str, customer_id: str, 
                       items: List[Dict[str, Any]]) -> Invoice:
        """
        Create an invoice.
        
        Args:
            provider: 'stripe' or 'square'
            customer_id: Customer ID in that provider
            items: List of dicts with 'description', 'amount', 'quantity'
        """
        return self._get_provider(provider).create_invoice(customer_id, items)
    
    def send_invoice(self, provider: str, invoice_id: str) -> Invoice:
        """Send/publish an invoice to the customer."""
        return self._get_provider(provider).send_invoice(invoice_id)
    
    def get_revenue(self, provider: str = "both", days: int = 30) -> Dict[str, Any]:
        """
        Get revenue summary.
        
        Args:
            provider: 'stripe', 'square', or 'both'
            days: Number of days to look back
        """
        if provider == "both":
            combined = {
                "period_days": days,
                "total_revenue": 0,
                "invoice_count": 0,
                "by_provider": {}
            }
            
            if self.stripe:
                try:
                    stripe_rev = self.stripe.get_revenue(days)
                    combined["by_provider"]["stripe"] = stripe_rev
                    combined["total_revenue"] += stripe_rev["total_revenue"]
                    combined["invoice_count"] += stripe_rev["invoice_count"]
                except Exception as e:
                    logger.warning(f"Stripe revenue failed: {e}")
            
            if self.square:
                try:
                    square_rev = self.square.get_revenue(days)
                    combined["by_provider"]["square"] = square_rev
                    combined["total_revenue"] += square_rev["total_revenue"]
                    combined["invoice_count"] += square_rev["invoice_count"]
                except Exception as e:
                    logger.warning(f"Square revenue failed: {e}")
            
            return combined
        
        return self._get_provider(provider).get_revenue(days)
    
    def search_invoices(self, query: str, limit: int = 25) -> List[Invoice]:
        """
        Search invoices across all providers by customer name/email.
        
        Args:
            query: Search term (matches customer name or email)
            limit: Max results
        """
        all_invoices = self.list_invoices(provider="both", limit=100)
        query_lower = query.lower()
        
        matches = [
            inv for inv in all_invoices
            if query_lower in inv.customer_name.lower() or
               (inv.customer_email and query_lower in inv.customer_email.lower())
        ]
        
        return matches[:limit]
    
    def get_status(self) -> Dict[str, Any]:
        """Get connection status for configured providers."""
        status = {
            "stripe": {"configured": bool(self.stripe_key), "connected": False},
            "square": {"configured": bool(self.square_token), "connected": False}
        }
        
        if self.stripe_key:
            try:
                self.stripe.stripe.Customer.list(limit=1)
                status["stripe"]["connected"] = True
            except Exception as e:
                status["stripe"]["error"] = str(e)
        
        if self.square_token:
            try:
                # Try modern SDK first
                if hasattr(self.square.client.locations, 'list'):
                    self.square.client.locations.list()
                else:
                    self.square.client.locations.list_locations()
                status["square"]["connected"] = True
            except Exception as e:
                status["square"]["error"] = str(e)
        
        return status


# ══════════════════════════════════════════════════════════════════════════════
# INVOICE EXTRACTION (invoice2data)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ExtractedInvoice:
    """Invoice data extracted from a PDF."""
    invoice_number: Optional[str] = None
    date: Optional[str] = None
    due_date: Optional[str] = None
    issuer: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    lines: List[Dict[str, Any]] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)


class InvoiceExtractor:
    """
    Extract structured data from invoice PDFs using invoice2data.
    
    Requires: pip install invoice2data
    Optional: poppler-utils for pdftotext, tesseract for OCR
    """
    
    def __init__(self, templates_dir: str = None):
        self.templates_dir = templates_dir
        self._invoice2data = None
    
    @property
    def invoice2data(self):
        if self._invoice2data is None:
            try:
                from invoice2data import extract_data
                from invoice2data.extract.loader import read_templates
                self._invoice2data = extract_data
                self._read_templates = read_templates
            except ImportError:
                raise ImportError("invoice2data not installed. Run: pip install invoice2data")
        return self._invoice2data
    
    def extract(self, pdf_path: str) -> ExtractedInvoice:
        """
        Extract invoice data from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ExtractedInvoice with parsed data
        """
        try:
            # Load templates
            templates = None
            if self.templates_dir:
                templates = self._read_templates(self.templates_dir)
            
            # Extract data
            result = self.invoice2data(pdf_path, templates=templates)
            
            if not result:
                return ExtractedInvoice(raw_data={"error": "No data extracted"})
            
            return ExtractedInvoice(
                invoice_number=result.get("invoice_number"),
                date=str(result.get("date")) if result.get("date") else None,
                due_date=str(result.get("due_date")) if result.get("due_date") else None,
                issuer=result.get("issuer"),
                amount=float(result.get("amount", 0)) if result.get("amount") else None,
                currency=result.get("currency"),
                lines=result.get("lines", []),
                raw_data=result
            )
        except Exception as e:
            logger.error(f"Invoice extraction error: {e}")
            return ExtractedInvoice(raw_data={"error": str(e)})
    
    def extract_batch(self, pdf_paths: List[str]) -> List[ExtractedInvoice]:
        """Extract data from multiple PDFs."""
        return [self.extract(path) for path in pdf_paths]


# ══════════════════════════════════════════════════════════════════════════════
# INVOICE GENERATION (HTML/PDF)
# ══════════════════════════════════════════════════════════════════════════════

# HTML Template based on sparksuite/simple-html-invoice-template
INVOICE_HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Invoice {invoice_number}</title>
    <style>
        .invoice-box {{
            max-width: 800px;
            margin: auto;
            padding: 30px;
            border: 1px solid #eee;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.15);
            font-size: 16px;
            line-height: 24px;
            font-family: 'Helvetica Neue', 'Helvetica', Helvetica, Arial, sans-serif;
            color: #555;
        }}
        .invoice-box table {{
            width: 100%;
            line-height: inherit;
            text-align: left;
        }}
        .invoice-box table td {{
            padding: 5px;
            vertical-align: top;
        }}
        .invoice-box table tr td:nth-child(2) {{
            text-align: right;
        }}
        .invoice-box table tr.top table td {{
            padding-bottom: 20px;
        }}
        .invoice-box table tr.top table td.title {{
            font-size: 45px;
            line-height: 45px;
            color: #333;
        }}
        .invoice-box table tr.information table td {{
            padding-bottom: 40px;
        }}
        .invoice-box table tr.heading td {{
            background: #eee;
            border-bottom: 1px solid #ddd;
            font-weight: bold;
        }}
        .invoice-box table tr.details td {{
            padding-bottom: 20px;
        }}
        .invoice-box table tr.item td {{
            border-bottom: 1px solid #eee;
        }}
        .invoice-box table tr.item.last td {{
            border-bottom: none;
        }}
        .invoice-box table tr.total td:nth-child(2) {{
            border-top: 2px solid #eee;
            font-weight: bold;
        }}
        @media only screen and (max-width: 600px) {{
            .invoice-box table tr.top table td,
            .invoice-box table tr.information table td {{
                width: 100%;
                display: block;
                text-align: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="invoice-box">
        <table cellpadding="0" cellspacing="0">
            <tr class="top">
                <td colspan="2">
                    <table>
                        <tr>
                            <td class="title">
                                {company_name}
                            </td>
                            <td>
                                Invoice #: {invoice_number}<br />
                                Created: {date}<br />
                                Due: {due_date}
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>

            <tr class="information">
                <td colspan="2">
                    <table>
                        <tr>
                            <td>
                                {company_name}<br />
                                {company_address}
                            </td>
                            <td>
                                {customer_name}<br />
                                {customer_email}
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>

            <tr class="heading">
                <td>Item</td>
                <td>Price</td>
            </tr>

            {items_html}

            <tr class="total">
                <td></td>
                <td>Total: {currency}{total}</td>
            </tr>
        </table>
    </div>
</body>
</html>'''


class InvoiceGenerator:
    """
    Generate professional HTML/PDF invoices.
    
    Based on sparksuite/simple-html-invoice-template.
    """
    
    def __init__(
        self,
        company_name: str = "Who Visions LLC",
        company_address: str = ""
    ):
        self.company_name = company_name
        self.company_address = company_address
    
    def generate_html(
        self,
        invoice_number: str,
        customer_name: str,
        customer_email: str,
        items: List[Dict[str, Any]],
        date: str = None,
        due_date: str = None,
        currency: str = "$"
    ) -> str:
        """
        Generate an HTML invoice.
        
        Args:
            invoice_number: Unique invoice ID
            customer_name: Customer's name
            customer_email: Customer's email
            items: List of dicts with 'description', 'amount', 'quantity'
            date: Invoice date (defaults to today)
            due_date: Payment due date
            currency: Currency symbol
            
        Returns:
            HTML string
        """
        from datetime import datetime
        
        if not date:
            date = datetime.now().strftime("%B %d, %Y")
        if not due_date:
            due_date = (datetime.now() + timedelta(days=30)).strftime("%B %d, %Y")
        
        # Build items HTML
        items_html = []
        total = 0
        for i, item in enumerate(items):
            amount = float(item.get("amount", 0))
            qty = int(item.get("quantity", 1))
            line_total = amount * qty
            total += line_total
            
            is_last = "last" if i == len(items) - 1 else ""
            items_html.append(f'''
            <tr class="item {is_last}">
                <td>{item.get("description", "Item")}</td>
                <td>{currency}{line_total:.2f}</td>
            </tr>''')
        
        # Render template
        html = INVOICE_HTML_TEMPLATE.format(
            invoice_number=invoice_number,
            company_name=self.company_name,
            company_address=self.company_address.replace("\n", "<br />"),
            customer_name=customer_name,
            customer_email=customer_email,
            date=date,
            due_date=due_date,
            items_html="".join(items_html),
            currency=currency,
            total=f"{total:.2f}"
        )
        
        return html
    
    def save_html(self, html: str, output_path: str) -> str:
        """Save HTML invoice to file."""
        from pathlib import Path
        Path(output_path).write_text(html, encoding="utf-8")
        logger.info(f"Invoice saved to {output_path}")
        return output_path
    
    def generate_pdf(
        self,
        invoice_number: str,
        customer_name: str,
        customer_email: str,
        items: List[Dict[str, Any]],
        output_path: str,
        **kwargs
    ) -> str:
        """
        Generate a PDF invoice.
        
        Requires: pip install weasyprint (or pdfkit + wkhtmltopdf)
        """
        html = self.generate_html(
            invoice_number=invoice_number,
            customer_name=customer_name,
            customer_email=customer_email,
            items=items,
            **kwargs
        )
        
        # Try weasyprint first, then pdfkit
        try:
            from weasyprint import HTML
            HTML(string=html).write_pdf(output_path)
            logger.info(f"PDF invoice saved to {output_path}")
            return output_path
        except ImportError:
            pass
        
        try:
            import pdfkit
            pdfkit.from_string(html, output_path)
            logger.info(f"PDF invoice saved to {output_path}")
            return output_path
        except ImportError:
            raise ImportError("Install weasyprint or pdfkit for PDF generation")
    
    def from_invoice(self, invoice: Invoice, output_path: str = None) -> str:
        """
        Generate HTML from an existing Invoice object.
        
        Args:
            invoice: Invoice dataclass instance
            output_path: If provided, saves to file
            
        Returns:
            HTML string (or file path if output_path provided)
        """
        items = [
            {"description": item.description, "amount": item.amount, "quantity": item.quantity}
            for item in invoice.items
        ] if invoice.items else [{"description": "Service", "amount": invoice.amount_due}]
        
        html = self.generate_html(
            invoice_number=invoice.id,
            customer_name=invoice.customer_name,
            customer_email=invoice.customer_email or "",
            items=items,
            date=invoice.created_at.strftime("%B %d, %Y"),
            due_date=invoice.due_date.strftime("%B %d, %Y") if invoice.due_date else None,
            currency="$" if invoice.currency == "usd" else invoice.currency.upper() + " "
        )
        
        if output_path:
            return self.save_html(html, output_path)
        return html

