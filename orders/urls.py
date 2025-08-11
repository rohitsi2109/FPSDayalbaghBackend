from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserOrderViewSet, AdminOrderViewSet

user_router = DefaultRouter()
user_router.register(r"me/orders", UserOrderViewSet, basename="me-orders")

admin_router = DefaultRouter()
admin_router.register(r"admin/orders", AdminOrderViewSet, basename="admin-orders")

urlpatterns = [
    path("", include(user_router.urls)),
    path("", include(admin_router.urls)),
]
