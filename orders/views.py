from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime
from .models import Order, OrderStatus
from .serializers import OrderSerializer, OrderCreateSerializer, OrderItemSerializer


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj: Order):
        return request.user and (request.user.is_staff or obj.user_id == request.user.id)


class OrderViewSet(viewsets.ModelViewSet):
    """
    - POST /api/orders/            -> create (user)
    - GET  /api/orders/            -> list (user sees own; admin sees all)
    - GET  /api/orders/{id}/       -> retrieve (owner or admin)
    - PATCH /api/orders/{id}/status/ {status} -> admin updates status
    - POST /api/orders/{id}/cancel/          -> user cancels if still pending
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Order.objects.select_related("user").prefetch_related("items__product")
        # Admin sees all, users see their own
        if self.request.user.is_staff:
            qs = qs
        else:
            qs = qs.filter(user=self.request.user)

        # Optional filter by status ?status=PENDING
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def get_permissions(self):
        if self.action in ["partial_update", "update", "destroy"]:
            # disallow generic updates/deletes via default endpoints
            return [permissions.IsAdminUser()]
        if self.action in ["status", "list_all"]:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        self.check_object_permissions(request, obj)
        serializer = OrderSerializer(obj, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["patch"])
    def status(self, request, pk=None):
        """Admin: change status."""
        order = self.get_object()
        new_status = request.data.get("status")
        valid = {c for c, _ in OrderStatus.choices}
        if new_status not in valid:
            return Response({"detail": f"Invalid status. Use one of {sorted(list(valid))}."},
                            status=status.HTTP_400_BAD_REQUEST)
        order.status = new_status
        order.save(update_fields=["status"])
        return Response(OrderSerializer(order, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """User: cancel only if still pending."""
        order = self.get_object()
        if request.user.is_staff is False and order.user_id != request.user.id:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        if order.status != OrderStatus.PENDING:
            return Response({"detail": "Only pending orders can be cancelled."},
                            status=status.HTTP_400_BAD_REQUEST)
        order.status = OrderStatus.CANCELLED
        order.save(update_fields=["status"])
        return Response(OrderSerializer(order, context={"request": request}).data)


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = (Order.objects
              .select_related("user")
              .prefetch_related("items__product")
              .order_by("-created_at"))

        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)

        status_param = self.request.query_params.get("status")
        valid_status = {c for c, _ in OrderStatus.choices}
        if status_param in valid_status:
            qs = qs.filter(status=status_param)

        since = self.request.query_params.get("since")
        if since:
            dt = parse_datetime(since)
            if dt:
                qs = qs.filter(created_at__gte=dt)

        return qs

    def get_serializer_class(self):
        return OrderCreateSerializer if self.action == "create" else OrderSerializer
