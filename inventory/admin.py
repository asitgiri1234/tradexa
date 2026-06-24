from django.contrib import admin

from .models import Box, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "weight_kg", "created_at")
    search_fields = ("name", "sku")


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = ("name", "cost", "max_weight_kg", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
