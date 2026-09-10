"""
Rent/GST/TDS split calculations.

Design decision (confirmed): GST and TDS are calculated off the agreement's
total_rent and percentages, never entered or stored per vendor. This means
if an amendment changes total_rent, every allocation's amounts recalculate
automatically - nothing to update on the allocation rows themselves.
"""
from decimal import Decimal, ROUND_HALF_UP

TWO_DP = Decimal("0.01")


def round2(value: Decimal) -> Decimal:
    return value.quantize(TWO_DP, rounding=ROUND_HALF_UP)


def calculate_allocation_amounts(
    total_rent: Decimal,
    gst_percentage: Decimal,
    tds_percentage: Decimal,
    split_percentage: Decimal,
) -> dict:
    """
    Given the agreement-level rent/GST%/TDS% and one allocation's split%,
    return that allocation's rent, GST, TDS and net payable.
    """
    rent = total_rent * split_percentage / Decimal("100")
    gst_amount = rent * gst_percentage / Decimal("100")
    tds_amount = rent * tds_percentage / Decimal("100")
    net_payable = rent + gst_amount - tds_amount

    return {
        "calculated_rent": round2(rent),
        "calculated_gst": round2(gst_amount),
        "calculated_tds": round2(tds_amount),
        "net_payable": round2(net_payable),
    }
