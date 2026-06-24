from rest_framework import serializers

from .models import Box, Product


class ProductSerializer(serializers.ModelSerializer):
    volume_cm3 = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "length_cm",
            "width_cm",
            "height_cm",
            "weight_kg",
            "volume_cm3",
            "created_at",
        ]


class BoxSerializer(serializers.ModelSerializer):
    volume_cm3 = serializers.FloatField(read_only=True)

    class Meta:
        model = Box
        fields = [
            "id",
            "name",
            "length_cm",
            "width_cm",
            "height_cm",
            "max_weight_kg",
            "volume_cm3",
            "cost",
            "is_active",
        ]
