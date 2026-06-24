from django.db import models


class Product(models.Model):
    """A physical product that can be added to an order."""

    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    length_cm = models.FloatField()
    width_cm = models.FloatField()
    height_cm = models.FloatField()
    weight_kg = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def volume_cm3(self):
        """Bounding-box volume of a single unit in cubic centimetres."""
        return self.length_cm * self.width_cm * self.height_cm


class Box(models.Model):
    """A shipping box that an order can be packed into."""

    name = models.CharField(max_length=200)
    length_cm = models.FloatField()
    width_cm = models.FloatField()
    height_cm = models.FloatField()
    max_weight_kg = models.FloatField()
    cost = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["cost"]
        verbose_name_plural = "boxes"

    def __str__(self):
        return self.name

    @property
    def volume_cm3(self):
        """Internal volume of the box in cubic centimetres."""
        return self.length_cm * self.width_cm * self.height_cm
