from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.models import Box, Product
from inventory.serializers import BoxSerializer

from .models import BoxRecommendation, Order
from .serializers import (
    OrderCreateSerializer,
    OrderItemInputSerializer,
    OrderSerializer,
)
from .services.box_selector import recommend_box


def _serialize_recommendation(box, reason, totals, request):
    """Build the common recommendation payload shared by several endpoints."""
    box_data = (
        BoxSerializer(box, context={"request": request}).data if box else None
    )
    return {
        "recommended_box": box_data,
        "total_volume_cm3": totals["total_volume_cm3"],
        "total_weight_kg": totals["total_weight_kg"],
        "effective_volume_cm3": totals["effective_volume_cm3"],
        "item_count": totals["item_count"],
        "reason": reason,
    }


class OrderListCreateView(generics.ListCreateAPIView):
    """GET lists orders; POST /api/orders/ creates an order with items."""

    queryset = Order.objects.all().prefetch_related("items__product")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        read_serializer = OrderSerializer(order, context={"request": request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)


class OrderDetailView(generics.RetrieveAPIView):
    """GET /api/orders/<id>/ — order detail with recommendation."""

    queryset = Order.objects.all().prefetch_related("items__product")
    serializer_class = OrderSerializer


class OrderRecommendView(APIView):
    """POST /api/orders/<id>/recommend/ — (re)compute the recommendation."""

    def post(self, request, pk):
        try:
            order = Order.objects.prefetch_related("items__product").get(pk=pk)
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        box, reason, totals = recommend_box(order)
        BoxRecommendation.objects.update_or_create(
            order=order,
            defaults={
                "recommended_box": box,
                "total_volume_cm3": totals["total_volume_cm3"],
                "total_weight_kg": totals["total_weight_kg"],
                "reason": reason,
            },
        )
        return Response(_serialize_recommendation(box, reason, totals, request))


class RecommendPreviewView(APIView):
    """POST /api/recommend/preview/ — preview without creating an order.

    Body: ``{"items": [{"product_id": 1, "quantity": 2}]}``. Also returns the
    list of active boxes flagged with whether each one fits, so the UI can grey
    out boxes that don't.
    """

    def post(self, request):
        serializer = OrderItemInputSerializer(data=request.data.get("items", []), many=True)
        serializer.is_valid(raise_exception=True)

        product_map = {p.id: p for p in Product.objects.all()}
        pairs = [
            (product_map[item["product_id"]], item["quantity"])
            for item in serializer.validated_data
        ]

        box, reason, totals = recommend_box(pairs)
        payload = _serialize_recommendation(box, reason, totals, request)

        # Annotate every active box with a fits flag for the UI.
        effective_volume = totals["effective_volume_cm3"]
        total_weight = totals["total_weight_kg"]
        boxes = []
        for candidate in Box.objects.filter(is_active=True):
            box_data = BoxSerializer(candidate, context={"request": request}).data
            box_data["fits"] = (
                candidate.volume_cm3 >= effective_volume
                and candidate.max_weight_kg >= total_weight
                and totals["item_count"] > 0
            )
            box_data["is_recommended"] = bool(box and candidate.id == box.id)
            boxes.append(box_data)

        payload["boxes"] = boxes
        return Response(payload)
