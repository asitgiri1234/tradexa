"""Selection of the cheapest box that can hold an order."""

from inventory.models import Box

from .packing_calculator import calculate_totals, get_line_items

NO_FIT_REASON = "No suitable box — consider splitting the order"
EMPTY_REASON = "Add at least one item to get a box recommendation."


def item_fits_box(product, box):
    """True if a single unit of ``product`` physically fits inside ``box``.

    Both the item and the box are sorted by their three dimensions, which
    allows any axis-aligned rotation of the item: the smallest item side must
    fit the smallest box side, and so on. This catches the case a pure volume
    check misses — e.g. a long, thin item that has small volume but is longer
    than every side of an otherwise roomy box.
    """
    item = sorted((product.length_cm, product.width_cm, product.height_cm))
    inner = sorted((box.length_cm, box.width_cm, box.height_cm))
    return all(side <= edge for side, edge in zip(item, inner))


def order_fits_box(box, products, totals):
    """True if ``box`` can hold the order by volume, weight and dimensions.

    ``products`` is the list of distinct products in the order; every one must
    individually fit the box (rotation allowed), in addition to the box having
    enough volume (after the packing-efficiency factor) and weight capacity.
    """
    return (
        box.volume_cm3 >= totals["effective_volume_cm3"]
        and box.max_weight_kg >= totals["total_weight_kg"]
        and all(item_fits_box(product, box) for product in products)
    )


def recommend_box(order):
    """Return ``(Box or None, reason, totals)`` for the given order.

    ``order`` may be an ``Order`` instance or an iterable of
    ``(product, quantity)`` pairs.

    A box is a candidate when it satisfies :func:`order_fits_box`. The cheapest
    candidate wins; if none qualify, ``None`` and an explanatory reason are
    returned.
    """
    pairs = get_line_items(order)
    totals = calculate_totals(pairs)
    products = [product for product, _ in pairs]

    if totals["item_count"] == 0:
        return None, EMPTY_REASON, totals

    candidates = [
        box
        for box in Box.objects.filter(is_active=True)
        if order_fits_box(box, products, totals)
    ]

    if not candidates:
        return None, NO_FIT_REASON, totals

    best = min(candidates, key=lambda box: box.cost)

    reason = (
        f"{best.name} is the cheapest box (${best.cost}) that fits every item "
        f"by dimension, the effective volume of {totals['effective_volume_cm3']:,.0f} "
        f"cm³ and total weight of {totals['total_weight_kg']:g} kg."
    )
    return best, reason, totals
