from rest_framework import generics

from .models import Box, Product
from .serializers import BoxSerializer, ProductSerializer


class ProductListView(generics.ListAPIView):
    """GET /api/products/ — list all products."""

    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductDetailView(generics.RetrieveAPIView):
    """GET /api/products/<id>/ — product detail."""

    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class BoxListView(generics.ListAPIView):
    """GET /api/boxes/ — list all active boxes."""

    serializer_class = BoxSerializer

    def get_queryset(self):
        return Box.objects.filter(is_active=True)
