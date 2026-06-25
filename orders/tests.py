from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from inventory.models import Box, Product

from .models import BoxRecommendation, Order, OrderItem
from .serializers import OrderCreateSerializer
from .services.box_selector import (
    EMPTY_REASON,
    NO_FIT_REASON,
    item_fits_box,
    recommend_box,
)
from .services.packing_calculator import PACKING_EFFICIENCY, calculate_totals


def make_product(sku, l, w, h, kg, name="P"):
    return Product.objects.create(
        name=name, sku=sku, length_cm=l, width_cm=w, height_cm=h, weight_kg=kg
    )


def make_box(name, l, w, h, max_kg, cost, is_active=True):
    return Box.objects.create(
        name=name, length_cm=l, width_cm=w, height_cm=h,
        max_weight_kg=max_kg, cost=Decimal(str(cost)), is_active=is_active,
    )


class PackingCalculatorTests(TestCase):
    def test_totals_and_efficiency_factor(self):
        p = make_product("A", 10, 10, 10, 2.0)  # volume 1000
        totals = calculate_totals([(p, 2)])
        self.assertEqual(totals["total_volume_cm3"], 2000)
        self.assertEqual(totals["total_weight_kg"], 4.0)
        self.assertEqual(totals["item_count"], 2)
        # effective volume inflates by the packing-efficiency factor
        self.assertAlmostEqual(
            totals["effective_volume_cm3"], 2000 / PACKING_EFFICIENCY, places=2
        )

    def test_empty_order_totals(self):
        totals = calculate_totals([])
        self.assertEqual(totals["item_count"], 0)
        self.assertEqual(totals["total_volume_cm3"], 0)
        self.assertEqual(totals["effective_volume_cm3"], 0)


class BoxSelectorTests(TestCase):
    def test_cheapest_fitting_box_is_chosen(self):
        p = make_product("SMALL", 5, 5, 5, 0.2)  # volume 125
        make_box("Cheap", 20, 20, 20, 5, "2.40")
        make_box("Expensive", 25, 25, 25, 10, "9.90")
        box, reason, totals = recommend_box([(p, 1)])
        self.assertEqual(box.name, "Cheap")
        self.assertIn("Cheap", reason)

    def test_dimensional_fit_rejects_short_box(self):
        # 44cm keyboard must NOT go in a 30cm box even though volume allows it.
        kb = make_product("KB", 44, 14, 4, 1.1)  # volume 2464
        small = make_box("Small", 30, 22, 12, 3, "2.40")   # volume 7920 (>= eff)
        medium = make_box("Medium", 45, 35, 20, 8, "3.90")
        self.assertFalse(item_fits_box(kb, small))
        self.assertTrue(item_fits_box(kb, medium))
        box, _, _ = recommend_box([(kb, 1)])
        self.assertEqual(box.name, "Medium")

    def test_rotation_allowed_in_fit(self):
        # Item is 44 long but the box's longest side is 44 on a different axis.
        item = make_product("ROT", 44, 3, 3, 0.5)
        box = make_box("Fits", 5, 5, 44, 5, "1.00")
        self.assertTrue(item_fits_box(item, box))

    def test_weight_limit_excludes_box(self):
        heavy = make_product("HVY", 5, 5, 5, 10.0)  # tiny but 10kg
        make_box("Light", 50, 50, 50, 3, "2.00")    # roomy but only 3kg
        box, reason, _ = recommend_box([(heavy, 1)])
        self.assertIsNone(box)
        self.assertEqual(reason, NO_FIT_REASON)

    def test_no_box_when_item_too_large(self):
        huge = make_product("HUGE", 200, 200, 200, 1.0)
        make_box("Tiny", 10, 10, 10, 50, "1.00")
        box, reason, _ = recommend_box([(huge, 1)])
        self.assertIsNone(box)
        self.assertEqual(reason, NO_FIT_REASON)

    def test_empty_order_returns_prompt(self):
        box, reason, totals = recommend_box([])
        self.assertIsNone(box)
        self.assertEqual(reason, EMPTY_REASON)
        self.assertEqual(totals["item_count"], 0)


class OrderModelTests(TestCase):
    def test_reference_generated_from_pk(self):
        o = Order.objects.create()
        self.assertEqual(o.reference, f"ORD-{o.pk:05d}")

    def test_references_are_unique_and_sequential(self):
        a = Order.objects.create()
        b = Order.objects.create()
        self.assertNotEqual(a.reference, b.reference)
        self.assertEqual(b.pk, a.pk + 1)

    def test_explicit_reference_is_preserved(self):
        o = Order.objects.create(reference="ORD-CUSTOM")
        self.assertEqual(o.reference, "ORD-CUSTOM")


class OrderCreateSerializerTests(TestCase):
    def setUp(self):
        self.p = make_product("CB", 12, 8, 2, 0.08)
        make_box("Box", 30, 22, 12, 3, "2.40")

    def test_duplicate_products_are_merged(self):
        ser = OrderCreateSerializer(data={"items": [
            {"product_id": self.p.id, "quantity": 1},
            {"product_id": self.p.id, "quantity": 4},
        ]})
        ser.is_valid(raise_exception=True)
        order = ser.save()
        items = list(order.items.all())
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].quantity, 5)

    def test_recommendation_created_with_order(self):
        ser = OrderCreateSerializer(data={"items": [
            {"product_id": self.p.id, "quantity": 1},
        ]})
        ser.is_valid(raise_exception=True)
        order = ser.save()
        self.assertTrue(BoxRecommendation.objects.filter(order=order).exists())

    def test_empty_items_rejected(self):
        ser = OrderCreateSerializer(data={"items": []})
        self.assertFalse(ser.is_valid())

    def test_unknown_product_rejected(self):
        ser = OrderCreateSerializer(data={"items": [
            {"product_id": 999999, "quantity": 1},
        ]})
        self.assertFalse(ser.is_valid())


class OrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.kb = make_product("KB", 44, 14, 4, 1.1)
        self.small = make_box("Small", 30, 22, 12, 3, "2.40")
        self.medium = make_box("Medium", 45, 35, 20, 8, "3.90")

    def test_preview_returns_dimensional_fits_flags(self):
        res = self.client.post(
            "/api/recommend/preview/",
            {"items": [{"product_id": self.kb.id, "quantity": 1}]},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["recommended_box"]["name"], "Medium")
        fits = {b["name"]: b["fits"] for b in data["boxes"]}
        self.assertFalse(fits["Small"])  # too short for the 44cm keyboard
        self.assertTrue(fits["Medium"])

    def test_create_order_returns_reference_and_recommendation(self):
        res = self.client.post(
            "/api/orders/",
            {"items": [{"product_id": self.kb.id, "quantity": 1}]},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data["reference"].startswith("ORD-"))
        self.assertEqual(data["recommendation"]["recommended_box"]["name"], "Medium")

    def test_order_detail(self):
        order = Order.objects.create()
        OrderItem.objects.create(order=order, product=self.kb, quantity=1)
        res = self.client.get(f"/api/orders/{order.id}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["reference"], order.reference)

    def test_recommend_endpoint_persists_recommendation(self):
        order = Order.objects.create()
        OrderItem.objects.create(order=order, product=self.kb, quantity=1)
        res = self.client.post(f"/api/orders/{order.id}/recommend/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["recommended_box"]["name"], "Medium")
        self.assertTrue(BoxRecommendation.objects.filter(order=order).exists())

    def test_recommend_unknown_order_returns_404(self):
        res = self.client.post("/api/orders/999999/recommend/")
        self.assertEqual(res.status_code, 404)
