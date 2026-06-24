"""Selection of the cheapest box that can hold an order."""

from inventory.models import Box

from .packing_calculator import calculate_totals

NO_FIT_REASON = "No suitable box — consider splitting the order"


def recommend_box(order):
    """Return ``(Box or None, reason, totals)`` for the given order.

    ``order`` may be an ``Order`` instance or an iterable of
    ``(product, quantity)`` pairs (see ``calculate_totals``).

    A box is a candidate when its internal volume can hold the
    efficiency-adjusted item volume and its weight limit covers the total
    weight. The cheapest candidate wins.
    """
    totals = calculate_totals(order)
    effective_volume = totals["effective_volume_cm3"]
    total_weight = totals["total_weight_kg"]

    if totals["item_count"] == 0:
        return None, "Add at least one item to get a box recommendation.", totals

    candidates = [
        box
        for box in Box.objects.filter(is_active=True)
        if box.volume_cm3 >= effective_volume and box.max_weight_kg >= total_weight
    ]

    if not candidates:
        return None, NO_FIT_REASON, totals

    best = min(candidates, key=lambda box: box.cost)

    reason = (
        f"{best.name} is the cheapest box (${best.cost}) that fits the "
        f"effective volume of {effective_volume:,.0f} cm³ and total weight of "
        f"{total_weight:g} kg."
    )
    return best, reason, totals
