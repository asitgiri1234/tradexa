"""Management command to (re)seed Tradexa products and boxes."""

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from inventory.models import Box, Product

SEED_DIR = Path(settings.BASE_DIR) / "seed_data"


class Command(BaseCommand):
    help = "Clear existing products and boxes, then load fresh seed data."

    @transaction.atomic
    def handle(self, *args, **options):
        products_path = SEED_DIR / "products.json"
        boxes_path = SEED_DIR / "boxes.json"

        with products_path.open(encoding="utf-8") as fh:
            products = json.load(fh)
        with boxes_path.open(encoding="utf-8") as fh:
            boxes = json.load(fh)

        deleted_products = Product.objects.all().delete()[0]
        deleted_boxes = Box.objects.all().delete()[0]
        self.stdout.write(
            f"Cleared {deleted_products} product(s) and {deleted_boxes} box(es)."
        )

        Product.objects.bulk_create([Product(**row) for row in products])
        Box.objects.bulk_create([Box(**row) for row in boxes])

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(products)} product(s) and {len(boxes)} box(es)."
            )
        )
