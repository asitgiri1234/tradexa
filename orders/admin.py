from django.contrib import admin

from .models import BoxRecommendation, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("reference",)
    inlines = [OrderItemInline]


@admin.register(BoxRecommendation)
class BoxRecommendationAdmin(admin.ModelAdmin):
    list_display = ("order", "recommended_box", "created_at")
