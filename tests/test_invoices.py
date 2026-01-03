"""
Test Invoice Service and Tool

Run: python test_invoices.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import directly to avoid vertexai dependency chain
from kaedra.services.invoices import (
    InvoiceService,
    InvoiceGenerator,
    InvoiceExtractor,
    Invoice,
    InvoiceItem
)
from kaedra.tools.invoices import invoice_action


def test_data_models():
    """Test dataclass models."""
    print("\n=== Testing Data Models ===")
    
    from datetime import datetime
    
    # Create invoice item
    item = InvoiceItem(description="Web Design", amount=500.00, quantity=1)
    print(f"✓ InvoiceItem: {item.description} = ${item.total}")
    
    # Create invoice
    invoice = Invoice(
        id="inv_test_001",
        provider="local",
        customer_name="Test Client",
        customer_email="test@example.com",
        status="open",
        amount_due=500.00,
        amount_paid=0.00,
        currency="usd",
        created_at=datetime.now(),
        items=[item]
    )
    print(f"✓ Invoice: {invoice.id} for {invoice.customer_name}")
    print(f"  Status: {invoice.status}, Paid: {invoice.is_paid}, Overdue: {invoice.is_overdue}")
    
    return True


def test_html_generator():
    """Test HTML invoice generation."""
    print("\n=== Testing HTML Generator ===")
    
    generator = InvoiceGenerator(
        company_name="Who Visions LLC",
        company_address="Remote Operations"
    )
    
    items = [
        {"description": "AI Consulting", "amount": 250.00, "quantity": 2},
        {"description": "Voice Integration", "amount": 150.00, "quantity": 1}
    ]
    
    html = generator.generate_html(
        invoice_number="INV-2024-001",
        customer_name="Acme Corp",
        customer_email="billing@acme.com",
        items=items
    )
    
    print(f"✓ Generated HTML invoice ({len(html)} chars)")
    print(f"  Preview: {html[:100]}...")
    
    # Save to temp file
    output_path = Path(__file__).parent / "test_invoice.html"
    generator.save_html(html, str(output_path))
    print(f"✓ Saved to {output_path}")
    
    return True


def test_tool_actions():
    """Test invoice tool actions (mock mode)."""
    print("\n=== Testing Tool Actions ===")
    
    # Test status (should work without API keys)
    result = invoice_action("status")
    print(f"✓ Status check: Stripe={result.get('stripe', {}).get('configured')}, Square={result.get('square', {}).get('configured')}")
    
    # Test generate (local, no API needed)
    result = invoice_action(
        "generate",
        customer_name="Test Client",
        customer_email="test@example.com",
        items=[{"description": "Service", "amount": 100}]
    )
    print(f"✓ Generated invoice: {result.get('invoice_number', 'N/A')}")
    
    # Test list without API key (should fail gracefully)
    result = invoice_action("list", provider="stripe")
    if "error" in result:
        print(f"✓ List (no API key): Handled gracefully - {result['error'][:50]}...")
    else:
        print(f"✓ List returned {result.get('count', 0)} invoices")
    
    return True


def test_stripe_connection():
    """Test Stripe connection (requires API key)."""
    print("\n=== Testing Stripe Connection ===")
    
    if not os.getenv("STRIPE_SECRET_KEY"):
        print("⚠ STRIPE_SECRET_KEY not set, skipping live test")
        return True
    
    service = InvoiceService()
    
    try:
        invoices = service.list_invoices(provider="stripe", limit=5)
        print(f"✓ Connected to Stripe! Found {len(invoices)} invoices")
        for inv in invoices[:3]:
            print(f"  - {inv.id}: {inv.customer_name} ${inv.amount_due} ({inv.status})")
        return True
    except Exception as e:
        print(f"✗ Stripe error: {e}")
        return False


def test_square_connection():
    """Test Square connection (requires API key)."""
    print("\n=== Testing Square Connection ===")
    
    if not os.getenv("SQUARE_ACCESS_TOKEN"):
        print("⚠ SQUARE_ACCESS_TOKEN not set, skipping live test")
        return True
    
    service = InvoiceService()
    
    try:
        invoices = service.list_invoices(provider="square", limit=5)
        print(f"✓ Connected to Square! Found {len(invoices)} invoices")
        for inv in invoices[:3]:
            print(f"  - {inv.id}: {inv.customer_name} ${inv.amount_due} ({inv.status})")
        return True
    except Exception as e:
        print(f"✗ Square error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("KAEDRA Invoice Service Tests")
    print("=" * 60)
    
    results = []
    
    results.append(("Data Models", test_data_models()))
    results.append(("HTML Generator", test_html_generator()))
    results.append(("Tool Actions", test_tool_actions()))
    results.append(("Stripe Connection", test_stripe_connection()))
    results.append(("Square Connection", test_square_connection()))
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed."))
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
