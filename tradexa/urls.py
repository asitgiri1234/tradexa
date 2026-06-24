from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("inventory.urls")),
    path("api/", include("orders.urls")),
    path(
        "",
        TemplateView.as_view(template_name="dashboard/index.html"),
        name="dashboard",
    ),
]
