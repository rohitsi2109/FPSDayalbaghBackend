from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime

from .models import Order, OrderStatus
from .serializers import OrderSerializer, OrderCreateSerializer


def _filtered_queryset(request, base_qs):
    """
    Apply ?status= and ?since= filters.
    """
    # ?status=
    status_param = request.query_params.get("status")
    valid_status = {c for c, _ in OrderStatus.choices}
    if status_param in valid_status:
        base_qs = base_qs.filter(status=status_param)

    # ?since=2025-08-11T12:00:00Z (ISO8601)
    since = request.query_params.get("since")
    if since:
        dt = parse_datetime(since)
        if dt:
            base_qs = base_qs.filter(created_at__gte=dt)

    return base_qs


# ---------- USER API: /api/me/orders/ ----------
class UserOrderViewSet(viewsets.ModelViewSet):
    """
    User endpoints:
    - POST /api/me/orders/            -> create
    - GET  /api/me/orders/            -> list (only my orders)
    - GET  /api/me/orders/{id}/       -> retrieve (only my order)
    - POST /api/me/orders/{id}/cancel/-> cancel if pending (only my order)
    """
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]  # no PUT/PATCH/DELETE

    def get_queryset(self):
        qs = (
            Order.objects
            .filter(user=self.request.user)
            .select_related("user")
            .prefetch_related("items__product")
            .order_by("-created_at")
        )
        return _filtered_queryset(self.request, qs)

    def get_serializer_class(self):
        return OrderCreateSerializer if self.action == "create" else OrderSerializer

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()  # ensured to be user's own by queryset
        if order.status != OrderStatus.PENDING:
            return Response(
                {"detail": "Only pending orders can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = OrderStatus.CANCELLED
        order.save(update_fields=["status"])
        return Response(OrderSerializer(order, context={"request": request}).data)


class AdminOrderViewSet(viewsets.ModelViewSet):
    """
    Admin endpoints:
    - GET   /api/admin/orders/             -> list (all)
    - GET   /api/admin/orders/{id}/        -> retrieve (any)
    - PATCH /api/admin/orders/{id}/status/ -> change status
    - POST  /api/admin/orders/{id}/cancel/ -> cancel if pending
    (Admin does not create orders in this API)
    """
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ["get", "patch", "post", "head", "options"]  # no PUT/DELETE

    def get_queryset(self):
        qs = (
            Order.objects
            .select_related("user")
            .prefetch_related("items__product")
            .order_by("-created_at")
        )
        return _filtered_queryset(self.request, qs)

    def get_serializer_class(self):
        # Admin never creates via this API
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        return Response({"detail": 'Method "POST" not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=["patch"])
    def status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get("status")
        valid = {c for c, _ in OrderStatus.choices}
        if new_status not in valid:
            return Response(
                {"detail": f"Invalid status. Use one of {sorted(list(valid))}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = new_status
        order.save(update_fields=["status"])
        return Response(OrderSerializer(order, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status != OrderStatus.PENDING:
            return Response(
                {"detail": "Only pending orders can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = OrderStatus.CANCELLED
        order.save(update_fields=["status"])
        return Response(OrderSerializer(order, context={"request": request}).data)
