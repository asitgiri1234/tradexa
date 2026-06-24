from django.db import models
from django.db.models import Max

from inventory.models import Box, Product


class Order(models.Model):
    """A customer order made up of one or more line items."""

    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_PACKED = "packed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_PACKED, "Packed"),
    ]

    reference = models.CharField(max_length=50, unique=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.reference or f"Order #{self.pk}"

    def save(self, *args, **kwargs):
        """Auto-generate a sequential reference like ORD-00123."""
        if not self.reference:
            last_id = Order.objects.aggregate(max_id=Max("id"))["max_id"] or 0
            self.reference = f"ORD-{last_id + 1:05d}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """A single product line within an order."""

    order = models.ForeignKey(
        Order, related_name="items", on_delete=models.CASCADE
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class BoxRecommendation(models.Model):
    """The recommended box for an order plus the supporting figures."""

    order = models.OneToOneField(
        Order, related_name="recommendation", on_delete=models.CASCADE
    )
    recommended_box = models.ForeignKey(
        Box, null=True, blank=True, on_delete=models.SET_NULL
    )
    total_volume_cm3 = models.FloatField()
    total_weight_kg = models.FloatField()
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        box = self.recommended_box.name if self.recommended_box else "No box"
        return f"{self.order} → {box}"
