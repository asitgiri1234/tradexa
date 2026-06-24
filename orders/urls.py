from django.urls import path

from .views import (
    OrderDetailView,
    OrderListCreateView,
    OrderRecommendView,
    RecommendPreviewView,
)

urlpatterns = [
    path("orders/", OrderListCreateView.as_view(), name="order-list-create"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path(
        "orders/<int:pk>/recommend/",
        OrderRecommendView.as_view(),
        name="order-recommend",
    ),
    path(
        "recommend/preview/",
        RecommendPreviewView.as_view(),
        name="recommend-preview",
    ),
]
