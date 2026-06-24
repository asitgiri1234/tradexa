"""Volume and weight calculations for an order."""

# Real-world packing never achieves 100% space usage, so the raw bounding-box
# volume of the items is inflated to account for gaps and padding.
PACKING_EFFICIENCY = 0.8


def calculate_totals(order):
    """Return the aggregate figures for an order.

    Accepts either a persisted ``Order`` instance (its related ``items`` are
    used) or an iterable of ``(product, quantity)`` pairs, so the same logic
    backs both saved orders and the preview endpoint.

    Returns a dict with ``total_volume_cm3``, ``total_weight_kg``,
    ``effective_volume_cm3`` and ``item_count``.
    """
    pairs = get_line_items(order)

    total_volume_cm3 = 0.0
    total_weight_kg = 0.0
    item_count = 0

    for product, quantity in pairs:
        quantity = int(quantity)
        total_volume_cm3 += product.volume_cm3 * quantity
        total_weight_kg += product.weight_kg * quantity
        item_count += quantity

    effective_volume_cm3 = total_volume_cm3 / PACKING_EFFICIENCY if total_volume_cm3 else 0.0

    return {
        "total_volume_cm3": round(total_volume_cm3, 2),
        "total_weight_kg": round(total_weight_kg, 3),
        "effective_volume_cm3": round(effective_volume_cm3, 2),
        "item_count": item_count,
    }


def get_line_items(order):
    """Normalise the input into a list of ``(product, quantity)`` tuples.

    Accepts an ``Order`` instance (reads its related ``items``) or an iterable
    of ``(product, quantity)`` pairs, so callers can share one representation.
    """
    items = getattr(order, "items", None)
    if items is not None and hasattr(items, "all"):
        return [(item.product, item.quantity) for item in items.select_related("product").all()]
    # Already an iterable of (product, quantity) pairs.
    return list(order)
