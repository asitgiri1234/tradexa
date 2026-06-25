from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from .models import Box, Product


class ProductModelTests(TestCase):
    def test_volume_property(self):
        product = Product.objects.create(
            name="Cube", sku="CUBE-1",
            length_cm=10, width_cm=5, height_cm=2, weight_kg=1.0,
        )
        self.assertEqual(product.volume_cm3, 100)

    def test_sku_is_unique(self):
        Product.objects.create(
            name="A", sku="DUP", length_cm=1, width_cm=1, height_cm=1, weight_kg=1
        )
        with self.assertRaises(Exception):
            Product.objects.create(
                name="B", sku="DUP", length_cm=1, width_cm=1, height_cm=1, weight_kg=1
            )


class BoxModelTests(TestCase):
    def test_volume_property(self):
        box = Box.objects.create(
            name="B", length_cm=10, width_cm=10, height_cm=10,
            max_weight_kg=5, cost=Decimal("2.00"),
        )
        self.assertEqual(box.volume_cm3, 1000)


class InventoryApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.product = Product.objects.create(
            name="Mouse", sku="MS-1",
            length_cm=12, width_cm=7, height_cm=4, weight_kg=0.12,
        )
        self.active_box = Box.objects.create(
            name="Active", length_cm=30, width_cm=20, height_cm=10,
            max_weight_kg=3, cost=Decimal("2.40"), is_active=True,
        )
        self.inactive_box = Box.objects.create(
            name="Inactive", length_cm=30, width_cm=20, height_cm=10,
            max_weight_kg=3, cost=Decimal("2.40"), is_active=False,
        )

    def test_product_list(self):
        res = self.client.get("/api/products/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(res.json()[0]["sku"], "MS-1")

    def test_product_detail(self):
        res = self.client.get(f"/api/products/{self.product.id}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["volume_cm3"], 12 * 7 * 4)

    def test_box_list_only_active(self):
        res = self.client.get("/api/boxes/")
        self.assertEqual(res.status_code, 200)
        names = [b["name"] for b in res.json()]
        self.assertIn("Active", names)
        self.assertNotIn("Inactive", names)
