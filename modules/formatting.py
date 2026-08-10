def to_crore(value):
    """Convert rupees to crore."""
    try:
        return float(value) / 10_000_000
    except (TypeError, ValueError):
        return 0.0


def format_crore(value, decimals=2):
    """Format rupee amount as ₹ Crore."""
    try:
        return f"₹{float(value) / 10_000_000:,.{decimals}f} Cr"
    except (TypeError, ValueError):
        return "₹0.00 Cr"


def format_cover(value):
    """Format cover ratio."""
    try:
        return f"{float(value):.2f}x"
    except (TypeError, ValueError):
        return "0.00x"