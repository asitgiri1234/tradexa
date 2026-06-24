from django.urls import path

from .views import BoxListView, ProductDetailView, ProductListView

urlpatterns = [
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("boxes/", BoxListView.as_view(), name="box-list"),
]
