"""
KAEDRA Invoice Tool - Voice-accessible invoice operations.

Exposes invoice functions to the Kaedra agent via [TOOL: ...] pattern.
"""

from typing import Dict, Any, List, Optional
import json
import time
import hashlib
from dataclasses import asdict
from functools import lru_cache

from kaedra.services.invoices import (
    InvoiceService,
    InvoiceGenerator,
    InvoiceExtractor,
    Invoice
)


# ═══════════════════════════════════════════════════════════════════════════════
# CACHING LAYER
# ═══════════════════════════════════════════════════════════════════════════════

# Cache storage with TTL
_cache: Dict[str, Dict[str, Any]] = {}
_cache_ttl_seconds = 60  # Cache for 60 seconds


def _get_cache_key(action: str, provider: str, **kwargs) -> str:
    """Generate a unique cache key for the request."""
    params = json.dumps(kwargs, sort_keys=True, default=str)
    key_str = f"{action}:{provider}:{params}"
    return hashlib.md5(key_str.encode()).hexdigest()


def _get_cached(key: str) -> Optional[Dict[str, Any]]:
    """Get cached result if still valid."""
    if key in _cache:
        entry = _cache[key]
        if time.time() - entry["timestamp"] < _cache_ttl_seconds:
            entry["result"]["_cached"] = True
            return entry["result"]
        else:
            del _cache[key]
    return None


def _set_cache(key: str, result: Dict[str, Any]) -> None:
    """Store result in cache."""
    _cache[key] = {
        "timestamp": time.time(),
        "result": result
    }


def clear_invoice_cache() -> Dict[str, Any]:
    """Clear all cached invoice data."""
    global _cache
    count = len(_cache)
    _cache = {}
    return {"cleared": count}


# Singleton service instance for connection reuse
_service_instance: Optional[InvoiceService] = None


def _get_service() -> InvoiceService:
    """Get or create singleton InvoiceService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = InvoiceService()
    return _service_instance


def invoice_action(
    action: str,
    provider: str = "stripe",
    **kwargs
) -> Dict[str, Any]:
    """
    Execute invoice operations.
    
    Actions:
        - list: List invoices (status, limit)
        - get: Get single invoice (invoice_id)
        - create: Create invoice (customer_id, items)
        - send: Send invoice (invoice_id)
        - revenue: Get revenue summary (days)
        - search: Search invoices (query)
        - status: Check provider connection status
        - generate: Generate local invoice HTML (customer_name, customer_email, items)
        - extract: Extract data from PDF (pdf_path)
        - clear_cache: Clear cached data
    
    Args:
        action: Operation to perform
        provider: 'stripe', 'square', or 'both'
        **kwargs: Action-specific parameters
        
    Returns:
        Dict with results or error
    """
    # Handle cache clear action
    if action == "clear_cache":
        return clear_invoice_cache()
    
    # Check cache for read operations
    cacheable_actions = {"list", "revenue", "status", "search"}
    cache_key = None
    
    if action in cacheable_actions:
        cache_key = _get_cache_key(action, provider, **kwargs)
        cached = _get_cached(cache_key)
        if cached:
            return cached
    
    service = _get_service()
    
    try:
        if action == "list":
            invoices = service.list_invoices(
                provider=provider,
                status=kwargs.get("status"),
                limit=kwargs.get("limit", 25)
            )
            result = {
                "action": "list",
                "provider": provider,
                "count": len(invoices),
                "invoices": [_invoice_to_dict(inv) for inv in invoices]
            }
            if cache_key:
                _set_cache(cache_key, result)
            return result
        
        elif action == "get":
            invoice_id = kwargs.get("invoice_id")
            if not invoice_id:
                return {"error": "invoice_id is required"}
            
            invoice = service.get_invoice(provider, invoice_id)
            return {
                "action": "get",
                "invoice": _invoice_to_dict(invoice)
            }
        
        elif action == "create":
            customer_id = kwargs.get("customer_id")
            items = kwargs.get("items", [])
            
            if not customer_id:
                return {"error": "customer_id is required"}
            if not items:
                return {"error": "items list is required"}
            
            invoice = service.create_invoice(provider, customer_id, items)
            return {
                "action": "create",
                "invoice": _invoice_to_dict(invoice),
                "message": f"Invoice {invoice.id} created successfully"
            }
        
        elif action == "send":
            invoice_id = kwargs.get("invoice_id")
            if not invoice_id:
                return {"error": "invoice_id is required"}
            
            invoice = service.send_invoice(provider, invoice_id)
            return {
                "action": "send",
                "invoice": _invoice_to_dict(invoice),
                "message": f"Invoice {invoice.id} sent to {invoice.customer_email}"
            }
        
        elif action == "revenue":
            days = kwargs.get("days", 30)
            rev_result = service.get_revenue(provider=provider, days=days)
            result = {
                "action": "revenue",
                **rev_result
            }
            if cache_key:
                _set_cache(cache_key, result)
            return result
        
        elif action == "search":
            query = kwargs.get("query")
            if not query:
                return {"error": "query is required"}
            
            invoices = service.search_invoices(query, limit=kwargs.get("limit", 25))
            result = {
                "action": "search",
                "query": query,
                "count": len(invoices),
                "invoices": [_invoice_to_dict(inv) for inv in invoices]
            }
            if cache_key:
                _set_cache(cache_key, result)
            return result
        
        elif action == "status":
            result = {
                "action": "status",
                **service.get_status()
            }
            if cache_key:
                _set_cache(cache_key, result)
            return result
        
        elif action == "generate":
            # Generate local invoice without provider
            generator = InvoiceGenerator(
                company_name=kwargs.get("company_name", "Who Visions LLC")
            )
            
            customer_name = kwargs.get("customer_name")
            customer_email = kwargs.get("customer_email", "")
            items = kwargs.get("items", [])
            
            if not customer_name:
                return {"error": "customer_name is required"}
            if not items:
                return {"error": "items list is required"}
            
            # Generate unique invoice number
            from datetime import datetime
            invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            html = generator.generate_html(
                invoice_number=invoice_number,
                customer_name=customer_name,
                customer_email=customer_email,
                items=items,
                date=kwargs.get("date"),
                due_date=kwargs.get("due_date")
            )
            
            # Optionally save
            output_path = kwargs.get("output_path")
            if output_path:
                if output_path.endswith(".pdf"):
                    path = generator.generate_pdf(
                        invoice_number=invoice_number,
                        customer_name=customer_name,
                        customer_email=customer_email,
                        items=items,
                        output_path=output_path,
                        date=kwargs.get("date"),
                        due_date=kwargs.get("due_date")
                    )
                else:
                    path = generator.save_html(html, output_path)
                return {
                    "action": "generate",
                    "invoice_number": invoice_number,
                    "saved_to": path
                }
            
            return {
                "action": "generate",
                "invoice_number": invoice_number,
                "html": html[:500] + "..." if len(html) > 500 else html
            }
        
        elif action == "extract":
            pdf_path = kwargs.get("pdf_path")
            if not pdf_path:
                return {"error": "pdf_path is required"}
            
            extractor = InvoiceExtractor()
            result = extractor.extract(pdf_path)
            
            return {
                "action": "extract",
                "invoice_number": result.invoice_number,
                "date": result.date,
                "issuer": result.issuer,
                "amount": result.amount,
                "currency": result.currency,
                "lines": result.lines
            }
        
        else:
            return {"error": f"Unknown action: {action}"}
    
    except Exception as e:
        return {"error": str(e)}


def _invoice_to_dict(invoice: Invoice) -> Dict[str, Any]:
    """Convert Invoice dataclass to serializable dict."""
    return {
        "id": invoice.id,
        "provider": invoice.provider,
        "customer_name": invoice.customer_name,
        "customer_email": invoice.customer_email,
        "status": invoice.status,
        "amount_due": invoice.amount_due,
        "amount_paid": invoice.amount_paid,
        "currency": invoice.currency,
        "created_at": invoice.created_at.isoformat(),
        "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
        "url": invoice.url,
        "is_paid": invoice.is_paid,
        "is_overdue": invoice.is_overdue
    }


# Convenience functions for common operations
def list_open_invoices(provider: str = "both") -> Dict[str, Any]:
    """List all unpaid invoices."""
    return invoice_action("list", provider=provider, status="open")


def get_revenue_summary(days: int = 30) -> Dict[str, Any]:
    """Get revenue summary for the specified period."""
    return invoice_action("revenue", provider="both", days=days)


def search_client_invoices(client_name: str) -> Dict[str, Any]:
    """Search for invoices by client name."""
    return invoice_action("search", query=client_name)
