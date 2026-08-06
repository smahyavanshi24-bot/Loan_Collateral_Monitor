"""
calculations.py
Business calculations for collateral monitoring.
"""


def calculate_collateral_value(shares, price):
    """Calculate collateral value."""
    return shares * price


def calculate_cover(collateral_value, loan_amount):
    """Calculate security cover."""

    if loan_amount == 0:
        return 0

    return collateral_value / loan_amount


def compliance_status(current_cover, required_cover):
    """Return compliance status."""

    if current_cover >= required_cover:
        return "✅ Complied"

    return "❌ Shortfall"