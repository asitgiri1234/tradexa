from rest_framework import serializers

from inventory.models import Product
from inventory.serializers import BoxSerializer, ProductSerializer

from .models import BoxRecommendation, Order, OrderItem


class OrderItemInputSerializer(serializers.Serializer):
    """A single requested line item — used for create and preview."""

    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError(
                f"Product with id {value} does not exist."
            )
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity"]


class BoxRecommendationSerializer(serializers.ModelSerializer):
    recommended_box = BoxSerializer(read_only=True)

    class Meta:
        model = BoxRecommendation
        fields = [
            "recommended_box",
            "total_volume_cm3",
            "total_weight_kg",
            "reason",
            "created_at",
        ]


class OrderSerializer(serializers.ModelSerializer):
    """Read serializer for an order, including items and recommendation."""

    items = OrderItemSerializer(many=True, read_only=True)
    recommendation = BoxRecommendationSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "reference",
            "status",
            "created_at",
            "items",
            "recommendation",
        ]


class OrderCreateSerializer(serializers.Serializer):
    """Write serializer accepting ``{items: [{product_id, quantity}]}``."""

    items = OrderItemInputSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError(
                "An order must contain at least one item."
            )
        return value

    def create(self, validated_data):
        from .services.box_selector import recommend_box

        order = Order.objects.create()

        for item in validated_data["items"]:
            OrderItem.objects.create(
                order=order,
                product_id=item["product_id"],
                quantity=item["quantity"],
            )

        box, reason, totals = recommend_box(order)
        BoxRecommendation.objects.create(
            order=order,
            recommended_box=box,
            total_volume_cm3=totals["total_volume_cm3"],
            total_weight_kg=totals["total_weight_kg"],
            reason=reason,
        )
        return order


class PreviewItemResultSerializer(serializers.Serializer):
    """Echoes the resolved totals for the preview response."""

    total_volume_cm3 = serializers.FloatField()
    total_weight_kg = serializers.FloatField()
    effective_volume_cm3 = serializers.FloatField()
    item_count = serializers.IntegerField()
