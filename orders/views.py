# # from rest_framework import viewsets, permissions, status
# # from rest_framework.decorators import action
# # from rest_framework.response import Response
# # from django.utils.dateparse import parse_datetime
# #
# # from .models import Order, OrderStatus
# # from .serializers import OrderSerializer, OrderCreateSerializer
# # from django.conf import settings
# # from django.db.models import Q
# #
# # def _filtered_queryset(request, base_qs):
# #     """
# #     Apply ?status= and ?since= filters.
# #     """
# #     # ?status=
# #     status_param = request.query_params.get("status")
# #     valid_status = {c for c, _ in OrderStatus.choices}
# #     if status_param in valid_status:
# #         base_qs = base_qs.filter(status=status_param)
# #
# #     # ?since=2025-08-11T12:00:00Z (ISO8601)
# #     since = request.query_params.get("since")
# #     if since:
# #         dt = parse_datetime(since)
# #         if dt:
# #             base_qs = base_qs.filter(created_at__gte=dt)
# #
# #     return base_qs
# #
# #
# # # ---------- USER API: /api/me/orders/ ----------
# # class UserOrderViewSet(viewsets.ModelViewSet):
# #     """
# #     User endpoints:
# #     - POST /api/me/orders/            -> create
# #     - GET  /api/me/orders/            -> list (only my orders)
# #     - GET  /api/me/orders/{id}/       -> retrieve (only my order)
# #     - POST /api/me/orders/{id}/cancel/-> cancel if pending (only my order)
# #     """
# #     permission_classes = [permissions.IsAuthenticated]
# #     http_method_names = ["get", "post", "head", "options"]  # no PUT/PATCH/DELETE
# #
# #     def get_queryset(self):
# #         qs = (
# #             Order.objects
# #             .filter(user=self.request.user)
# #             .select_related("user")
# #             .prefetch_related("items__product")
# #             .order_by("-created_at")
# #         )
# #         return _filtered_queryset(self.request, qs)
# #
# #     def get_serializer_class(self):
# #         return OrderCreateSerializer if self.action == "create" else OrderSerializer
# #
# #     @action(detail=True, methods=["post"])
# #     def cancel(self, request, pk=None):
# #         order = self.get_object()  # ensured to be user's own by queryset
# #         if order.status != OrderStatus.PENDING:
# #             return Response(
# #                 {"detail": "Only pending orders can be cancelled."},
# #                 status=status.HTTP_400_BAD_REQUEST,
# #             )
# #         order.status = OrderStatus.CANCELLED
# #         order.save(update_fields=["status"])
# #         return Response(OrderSerializer(order, context={"request": request}).data)
# #
# #
# # class AdminOrderViewSet(viewsets.ModelViewSet):
# #     """
# #     Admin endpoints:
# #     - GET   /api/admin/orders/             -> list (all)
# #     - GET   /api/admin/orders/{id}/        -> retrieve (any)
# #     - PATCH /api/admin/orders/{id}/status/ -> change status
# #     - POST  /api/admin/orders/{id}/cancel/ -> cancel if pending
# #     (Admin does not create orders in this API)
# #     """
# #     permission_classes = [permissions.IsAdminUser]
# #     http_method_names = ["get", "patch", "post", "head", "options"]  # no PUT/DELETE
# #
# #     def get_queryset(self):
# #         qs = (
# #             Order.objects
# #             .select_related("user")
# #             .prefetch_related("items__product")
# #             .order_by("-created_at")
# #         )
# #         return _filtered_queryset(self.request, qs)
# #
# #     def get_serializer_class(self):
# #         # Admin never creates via this API
# #         return OrderSerializer
# #
# #     def create(self, request, *args, **kwargs):
# #         return Response({"detail": 'Method "POST" not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
# #
# #     @action(detail=True, methods=["patch"])
# #     def status(self, request, pk=None):
# #         order = self.get_object()
# #         new_status = request.data.get("status")
# #         valid = {c for c, _ in OrderStatus.choices}
# #         if new_status not in valid:
# #             return Response(
# #                 {"detail": f"Invalid status. Use one of {sorted(list(valid))}."},
# #                 status=status.HTTP_400_BAD_REQUEST,
# #             )
# #         order.status = new_status
# #         order.save(update_fields=["status"])
# #         return Response(OrderSerializer(order, context={"request": request}).data)
# #
# #     @action(detail=True, methods=["post"])
# #     def cancel(self, request, pk=None):
# #         order = self.get_object()
# #         if order.status != OrderStatus.PENDING:
# #             return Response(
# #                 {"detail": "Only pending orders can be cancelled."},
# #                 status=status.HTTP_400_BAD_REQUEST,
# #             )
# #         order.status = OrderStatus.CANCELLED
# #         order.save(update_fields=["status"])
# #         return Response(OrderSerializer(order, context={"request": request}).data)
#
#
#
# # orders/views.py
# from rest_framework import viewsets, permissions, status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from django.utils.dateparse import parse_datetime
#
# from .models import Order, OrderStatus
# from .serializers import OrderSerializer, OrderCreateSerializer
# from django.conf import settings
# from django.db.models import Q
#
#
# def _filtered_queryset(request, base_qs):
#     """
#     Apply ?status= and ?since= filters.
#     """
#     # ?status=
#     status_param = request.query_params.get("status")
#     valid_status = {c for c, _ in OrderStatus.choices}
#     if status_param in valid_status:
#         base_qs = base_qs.filter(status=status_param)
#
#     # ?since=2025-08-11T12:00:00Z (ISO8601)
#     since = request.query_params.get("since")
#     if since:
#         dt = parse_datetime(since)
#         if dt:
#             base_qs = base_qs.filter(created_at__gte=dt)
#
#     return base_qs
#
#
# # ---------- USER API: /api/me/orders/ ----------
# class UserOrderViewSet(viewsets.ModelViewSet):
#     """
#     User endpoints:
#     - POST /api/me/orders/            -> create
#     - GET  /api/me/orders/            -> list (my online + my POS-linked orders)
#     - GET  /api/me/orders/{id}/       -> retrieve (only my order)
#     - POST /api/me/orders/{id}/cancel/-> cancel if pending (only my own online order)
#     """
#     permission_classes = [permissions.IsAuthenticated]
#     http_method_names = ["get", "post", "head", "options"]  # no PUT/PATCH/DELETE
#
#     def get_queryset(self):
#         u = self.request.user
#         # Include: orders I own OR orders whose invoice.customer == me
#         # Optional: also include orders whose shipping_phone == my phone (toggle via settings)
#         phone_match_enabled = getattr(settings, "ORDERS_INCLUDE_SHIPPING_PHONE_MATCH", False)
#         user_phone = getattr(u, "phone", None)
#
#         phone_clause = (
#             Q(shipping_phone=user_phone)
#             if (phone_match_enabled and user_phone)
#             else Q(pk__in=[])  # no-op when disabled/missing phone
#         )
#
#         qs = (
#             Order.objects
#             .select_related("user")
#             .prefetch_related("items__product", "invoices")  # reverse FK: BillingInvoice(order, related_name="invoices")
#             .filter(
#                 Q(user=u) |
#                 Q(invoices__customer=u) |
#                 phone_clause
#             )
#             .distinct()  # avoid dupes if multiple related rows
#             .order_by("-created_at")
#         )
#         return _filtered_queryset(self.request, qs)
#
#     def get_serializer_class(self):
#         return OrderCreateSerializer if self.action == "create" else OrderSerializer
#
#     @action(detail=True, methods=["post"])
#     def cancel(self, request, pk=None):
#         # IMPORTANT: With the expanded queryset, ensure user can only cancel their *own* online orders
#         order = self.get_object()
#         if order.user_id != request.user.id:
#             return Response(
#                 {"detail": "You can only cancel your own online orders."},
#                 status=status.HTTP_403_FORBIDDEN,
#             )
#         if order.status != OrderStatus.PENDING:
#             return Response(
#                 {"detail": "Only pending orders can be cancelled."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         order.status = OrderStatus.CANCELLED
#         order.save(update_fields=["status"])
#         return Response(OrderSerializer(order, context={"request": request}).data)
#
#
# class AdminOrderViewSet(viewsets.ModelViewSet):
#     """
#     Admin endpoints:
#     - GET   /api/admin/orders/             -> list (all)
#     - GET   /api/admin/orders/{id}/        -> retrieve (any)
#     - PATCH /api/admin/orders/{id}/status/ -> change status
#     - POST  /api/admin/orders/{id}/cancel/ -> cancel if pending
#     (Admin does not create orders in this API)
#     """
#     permission_classes = [permissions.IsAdminUser]
#     http_method_names = ["get", "patch", "post", "head", "options"]  # no PUT/DELETE
#
#     def get_queryset(self):
#         qs = (
#             Order.objects
#             .select_related("user")
#             .prefetch_related("items__product", "invoices")
#             .order_by("-created_at")
#         )
#         return _filtered_queryset(self.request, qs)
#
#     def get_serializer_class(self):
#         # Admin never creates via this API
#         return OrderSerializer
#
#     def create(self, request, *args, **kwargs):
#         return Response({"detail": 'Method "POST" not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
#
#     @action(detail=True, methods=["patch"])
#     def status(self, request, pk=None):
#         order = self.get_object()
#         new_status = request.data.get("status")
#         valid = {c for c, _ in OrderStatus.choices}
#         if new_status not in valid:
#             return Response(
#                 {"detail": f"Invalid status. Use one of {sorted(list(valid))}."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         order.status = new_status
#         order.save(update_fields=["status"])
#         return Response(OrderSerializer(order, context={"request": request}).data)
#
#     @action(detail=True, methods=["post"])
#     def cancel(self, request, pk=None):
#         order = self.get_object()
#         if order.status != OrderStatus.PENDING:
#             return Response(
#                 {"detail": "Only pending orders can be cancelled."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         order.status = OrderStatus.CANCELLED
#         order.save(update_fields=["status"])
#         return Response(OrderSerializer(order, context={"request": request}).data)


#
# from rest_framework import viewsets, permissions, status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from django.utils.dateparse import parse_datetime
#
# from .models import Order, OrderStatus, OrderSource
# from .serializers import OrderSerializer, OrderCreateSerializer
# from django.conf import settings
# from django.db.models import Q
#
#
# def _filtered_queryset(request, base_qs):
#     """
#     Apply ?status=, ?since=, and ?source= filters.
#     """
#     # ?status=
#     status_param = request.query_params.get("status")
#     valid_status = {c for c, _ in OrderStatus.choices}
#     if status_param in valid_status:
#         base_qs = base_qs.filter(status=status_param)
#
#     # ?source=ONLINE|POS
#     source_param = request.query_params.get("source")
#     valid_source = {c for c, _ in OrderSource.choices}
#     if source_param in valid_source:
#         base_qs = base_qs.filter(source=source_param)
#
#     # ?since=2025-08-11T12:00:00Z (ISO8601)
#     since = request.query_params.get("since")
#     if since:
#         dt = parse_datetime(since)
#         if dt:
#             base_qs = base_qs.filter(created_at__gte=dt)
#
#     return base_qs
#
#
# # ---------- USER API: /api/me/orders/ ----------
# class UserOrderViewSet(viewsets.ModelViewSet):
#     """
#     User endpoints:
#     - POST /api/me/orders/            -> create
#     - GET  /api/me/orders/            -> list (my online + my POS-linked orders)
#     - GET  /api/me/orders/{id}/       -> retrieve (only my order)
#     - POST /api/me/orders/{id}/cancel/-> cancel if pending (only my own online order)
#     """
#     permission_classes = [permissions.IsAuthenticated]
#     http_method_names = ["get", "post", "head", "options"]  # no PUT/PATCH/DELETE
#
#     def get_queryset(self):
#         u = self.request.user
#         phone_match_enabled = getattr(settings, "ORDERS_INCLUDE_SHIPPING_PHONE_MATCH", False)
#         user_phone = getattr(u, "phone", None)
#
#         phone_clause = (
#             Q(shipping_phone=user_phone)
#             if (phone_match_enabled and user_phone)
#             else Q(pk__in=[])
#         )
#
#         qs = (
#             Order.objects
#             .select_related("user")
#             .prefetch_related("items__product", "invoices")
#             .filter(
#                 Q(user=u) |             # online orders placed by user
#                 Q(invoices__customer=u) # POS orders linked to user via invoice.customer
#                 | phone_clause          # optional shipping-phone match
#             )
#             .distinct()
#             .order_by("-created_at")
#         )
#         return _filtered_queryset(self.request, qs)
#
#     def get_serializer_class(self):
#         return OrderCreateSerializer if self.action == "create" else OrderSerializer
#
#     @action(detail=True, methods=["post"])
#     def cancel(self, request, pk=None):
#         # With expanded queryset, ensure user can only cancel their own ONLINE orders
#         order = self.get_object()
#         if order.user_id != request.user.id:
#             return Response(
#                 {"detail": "You can only cancel your own online orders."},
#                 status=status.HTTP_403_FORBIDDEN,
#             )
#         if order.status != OrderStatus.PENDING:
#             return Response(
#                 {"detail": "Only pending orders can be cancelled."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         order.status = OrderStatus.CANCELLED
#         order.save(update_fields=["status"])
#         return Response(OrderSerializer(order, context={"request": request}).data)
#
#
# class AdminOrderViewSet(viewsets.ModelViewSet):
#     """
#     Admin endpoints:
#     - GET   /api/admin/orders/             -> list (all; use ?source=ONLINE to see only online)
#     - GET   /api/admin/orders/{id}/        -> retrieve (any)
#     - PATCH /api/admin/orders/{id}/status/ -> change status
#     - POST  /api/admin/orders/{id}/cancel/ -> cancel if pending
#     (Admin does not create orders in this API)
#     """
#     permission_classes = [permissions.IsAdminUser]
#     http_method_names = ["get", "patch", "post", "head", "options"]  # no PUT/DELETE
#
#     def get_queryset(self):
#         qs = (
#             Order.objects
#             .select_related("user")
#             .prefetch_related("items__product", "invoices")
#             .order_by("-created_at")
#         )
#         return _filtered_queryset(self.request, qs)
#
#     def get_serializer_class(self):
#         return OrderSerializer
#
#     def create(self, request, *args, **kwargs):
#         return Response({"detail": 'Method "POST" not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
#
#     @action(detail=True, methods=["patch"])
#     def status(self, request, pk=None):
#         order = self.get_object()
#         new_status = request.data.get("status")
#         valid = {c for c, _ in OrderStatus.choices}
#         if new_status not in valid:
#             return Response(
#                 {"detail": f"Invalid status. Use one of {sorted(list(valid))}."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         order.status = new_status
#         order.save(update_fields=["status"])
#         return Response(OrderSerializer(order, context={"request": request}).data)
#
#     @action(detail=True, methods=["post"])
#     def cancel(self, request, pk=None):
#         order = self.get_object()
#         if order.status != OrderStatus.PENDING:
#             return Response(
#                 {"detail": "Only pending orders can be cancelled."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         order.status = OrderStatus.CANCELLED
#         order.save(update_fields=["status"])
#         return Response(OrderSerializer(order, context={"request": request}).data)





from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime

from .models import Order, OrderStatus, OrderSource
from .serializers import OrderSerializer, OrderCreateSerializer, UserOrderSerializer
from django.conf import settings
from django.db.models import Q


def _filtered_queryset(request, base_qs):
    """
    Apply ?status=, ?since=, and ?source= filters.
    """
    # ?status=
    status_param = request.query_params.get("status")
    valid_status = {c for c, _ in OrderStatus.choices}
    if status_param in valid_status:
        base_qs = base_qs.filter(status=status_param)

    # ?source=ONLINE|POS
    source_param = request.query_params.get("source")
    valid_source = {c for c, _ in OrderSource.choices}
    if source_param in valid_source:
        base_qs = base_qs.filter(source=source_param)

    # ?since=2025-08-11T12:00:00Z (ISO8601)
    since = request.query_params.get("since")
    if since:
        dt = parse_datetime(since)
        if dt:
            base_qs = base_qs.filter(updated_at__gte=dt)

    return base_qs


# ---------- USER API: /api/me/orders/ ----------
class UserOrderViewSet(viewsets.ModelViewSet):
    """
    User endpoints:
    - POST /api/me/orders/            -> create (online)
    - GET  /api/me/orders/            -> list (my online + my POS-linked orders)
    - GET  /api/me/orders/{id}/       -> retrieve
    - POST /api/me/orders/{id}/cancel/-> cancel if pending (only my own online order)
    """
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]  # no PUT/PATCH/DELETE

    def get_queryset(self):
        u = self.request.user
        phone_match_enabled = getattr(settings, "ORDERS_INCLUDE_SHIPPING_PHONE_MATCH", False)
        user_phone = getattr(u, "phone", None)

        phone_clause = (
            Q(shipping_phone=user_phone)
            if (phone_match_enabled and user_phone)
            else Q(pk__in=[])
        )

        qs = (
            Order.objects
            .select_related("user")
            .prefetch_related("items__product", "invoices")  # BillingInvoice(order, related_name="invoices")
            .filter(
                Q(user=u) |             # online orders placed by user
                Q(invoices__customer=u) # POS orders linked to user via invoice.customer
                | phone_clause          # optional shipping-phone match
            )
            .distinct()
            .order_by("-created_at")
        )
        return _filtered_queryset(self.request, qs)

    def get_serializer_class(self):
        # Use the user-facing serializer (labels POS nicely)
        return OrderCreateSerializer if self.action == "create" else UserOrderSerializer

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        # Ensure user can only cancel their own ONLINE orders
        order = self.get_object()
        if order.user_id != request.user.id:
            return Response(
                {"detail": "You can only cancel your own online orders."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if order.status != OrderStatus.PENDING:
            return Response(
                {"detail": "Only pending orders can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = OrderStatus.CANCELLED
        order.save(update_fields=["status"])
        return Response(OrderSerializer(order, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="remove-item")
    def remove_item(self, request, pk=None):
        order = self.get_object()
        if order.user_id != request.user.id:
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
        if order.status != OrderStatus.PENDING:
            return Response({"detail": "Only pending orders can be edited."}, status=status.HTTP_400_BAD_REQUEST)

        item_id = request.data.get("item_id")
        if not item_id:
            return Response({"detail": "item_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = order.items.get(id=item_id)
            product = item.product
            product.stock += item.quantity
            product.save(update_fields=["stock"])
            
            lt = item.line_total
            item.delete()
            
            order.total_amount -= lt
            if order.total_amount < 0: order.total_amount = 0
            order.save(update_fields=["total_amount"])
        except Exception:
            return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

        # Re-fetch to clear prefetch caches
        order = self.get_queryset().get(pk=order.pk)
        return Response(UserOrderSerializer(order, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="add-item")
    def add_item(self, request, pk=None):
        order = self.get_object()
        if order.user_id != request.user.id:
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
        if order.status != OrderStatus.PENDING:
            return Response({"detail": "Only pending orders can be edited."}, status=status.HTTP_400_BAD_REQUEST)

        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))
        if not product_id:
            return Response({"detail": "product_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        from products.models import Product
        try:
            product = Product.objects.get(id=product_id)
            if product.stock < quantity:
                return Response({"detail": "Not enough stock."}, status=status.HTTP_400_BAD_REQUEST)
            
            existing_item = order.items.filter(product=product).first()
            if existing_item:
                existing_item.quantity += quantity
                existing_item.line_total = existing_item.quantity * existing_item.unit_price
                existing_item.save(update_fields=["quantity", "line_total"])
            else:
                order.items.create(
                    product=product,
                    quantity=quantity,
                    unit_price=product.price,
                    line_total=product.price * quantity
                )
            
            product.stock -= quantity
            product.save(update_fields=["stock"])
            order.total_amount += (product.price * quantity)
            order.save(update_fields=["total_amount"])
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        order = self.get_queryset().get(pk=order.pk)
        return Response(UserOrderSerializer(order, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="update-item-quantity")
    def update_item_quantity(self, request, pk=None):
        order = self.get_object()
        if order.user_id != request.user.id:
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
        if order.status != OrderStatus.PENDING:
            return Response({"detail": "Only pending orders can be edited."}, status=status.HTTP_400_BAD_REQUEST)

        item_id = request.data.get("item_id")
        new_qty = int(request.data.get("quantity", 0))
        if not item_id or new_qty < 1:
            return Response({"detail": "Invalid item_id or quantity."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = order.items.get(id=item_id)
            product = item.product
            diff = new_qty - item.quantity
            
            if diff > 0:
                if product.stock < diff:
                    return Response({"detail": "Not enough stock."}, status=status.HTTP_400_BAD_REQUEST)
                product.stock -= diff
            else:
                product.stock += abs(diff)
            
            product.save(update_fields=["stock"])
            item.quantity = new_qty
            item.line_total = item.quantity * item.unit_price
            item.save(update_fields=["quantity", "line_total"])
            order.total_amount += (diff * item.unit_price)
            if order.total_amount < 0: order.total_amount = 0
            order.save(update_fields=["total_amount"])
        except Exception:
            return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

        order = self.get_queryset().get(pk=order.pk)
        return Response(UserOrderSerializer(order, context={"request": request}).data)


class AdminOrderViewSet(viewsets.ModelViewSet):
    """
    Admin endpoints:
    - GET   /api/admin/orders/             -> list (all; use ?source=ONLINE to see only online)
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
            .prefetch_related("items__product", "invoices")
            .order_by("-created_at")
        )
        return _filtered_queryset(self.request, qs)

    def get_serializer_class(self):
        # Admin sees the raw status (no UI overrides)
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

    @action(detail=True, methods=["post"], url_path="remove-item")
    def remove_item(self, request, pk=None):
        """
        Remove a specific item from the order.
        Body: {"item_id": 123}
        """
        order = self.get_object()
        item_id = request.data.get("item_id")
        
        if not item_id:
            return Response({"detail": "item_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Allow basic editing only if PENDING (or CONFIRMED, depending on policy)
        # Assuming we can edit as long as it's not Delivered/Cancelled
        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
             return Response({"detail": "Cannot edit completed/cancelled orders."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = order.items.get(id=item_id)
            # Restore stock? 
            # If we follow the create logic, stock was deducted. So we should restore it.
            product = item.product
            product.stock += item.quantity
            product.save(update_fields=["stock"])
            
            # Remove item
            item.delete()
            
            # Optional: Recalculate total? 
            # The Admin might overwrite it later, but keeping it consistent is good.
            # But the prompt says "admin set price", so maybe we leave it or decrease it.
            # Let's decrease it for correctness.
            order.total_amount -= item.line_total
            if order.total_amount < 0:
                order.total_amount = 0
            order.save(update_fields=["total_amount"])

        except (ValueError, item.DoesNotExist, Exception) as e:
            return Response({"detail": "Item not found or invalid."}, status=status.HTTP_404_NOT_FOUND)

        return Response(OrderSerializer(order, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="confirm-order")
    def confirm_order(self, request, pk=None):
        """
        Confirm order and optionally update price.
        Body: {"total_amount": 500.00}
        """
        order = self.get_object()
        
        # Only allow confirming if Pending
        if order.status != OrderStatus.PENDING:
            return Response({"detail": "Order is not in Pending state."}, status=status.HTTP_400_BAD_REQUEST)

        new_total = request.data.get("total_amount")
        if new_total is not None:
            order.total_amount = new_total
        
        order.status = OrderStatus.CONFIRMED
        order.save(update_fields=["status", "total_amount"])
        
        return Response(OrderSerializer(order, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="add-item")
    def add_item(self, request, pk=None):
        """
        Add a product to the order.
        Body: {"product_id": 12, "quantity": 1}
        """
        order = self.get_object()
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))

        if not product_id:
            return Response({"detail": "product_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
             return Response({"detail": "Cannot edit completed/cancelled orders."}, status=status.HTTP_400_BAD_REQUEST)

        from products.models import Product  # Lazy import to avoid circular dependency if any
        try:
            product = Product.objects.get(id=product_id)
            if product.stock < quantity:
                return Response({"detail": f"Not enough stock. Available: {product.stock}"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if item already exists
            existing_item = order.items.filter(product=product).first()
            if existing_item:
                existing_item.quantity += quantity
                existing_item.line_total = existing_item.quantity * existing_item.unit_price
                existing_item.save(update_fields=["quantity", "line_total"])
            else:
                unit_price = product.price # Snapshot price
                line_total = unit_price * quantity
                order.items.create(
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    line_total=line_total
                )
            
            # Deduct stock
            product.stock -= quantity
            product.save(update_fields=["stock"])

            # Update Order Total?
            # Keeping consistent with remove_item, let's update it.
            # But remember Confirm might overwrite it.
            order.total_amount += (product.price * quantity)
            order.save(update_fields=["total_amount"])

        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(OrderSerializer(order, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="update-item-quantity")
    def update_item_quantity(self, request, pk=None):
        """
        Update quantity of an existing item.
        Body: {"item_id": 123, "quantity": 5}
        """
        order = self.get_object()
        item_id = request.data.get("item_id")
        new_quantity = int(request.data.get("quantity", 0))

        if not item_id:
            return Response({"detail": "item_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if new_quantity < 1:
             return Response({"detail": "Quantity must be at least 1. Use remove-item to delete."}, status=status.HTTP_400_BAD_REQUEST)

        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
             return Response({"detail": "Cannot edit completed/cancelled orders."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = order.items.get(id=item_id)
            product = item.product
            
            diff = new_quantity - item.quantity
            
            if diff > 0: # Increasing quantity
                if product.stock < diff:
                    return Response({"detail": f"Not enough stock. Available: {product.stock}"}, status=status.HTTP_400_BAD_REQUEST)
                product.stock -= diff
            else: # Decreasing quantity
                product.stock += abs(diff) # Restore stock
            
            product.save(update_fields=["stock"])

            # Update item
            item.quantity = new_quantity
            item.line_total = item.quantity * item.unit_price
            item.save(update_fields=["quantity", "line_total"])

            # Update Order Total
            # We need to recalculate carefully or just add the diff * price
            # Diff calculation:
            order.total_amount += (diff * item.unit_price)
            if order.total_amount < 0: order.total_amount = 0
            order.save(update_fields=["total_amount"])

        except (ValueError, item.DoesNotExist, Exception) as e:
            return Response({"detail": "Item not found or invalid."}, status=status.HTTP_404_NOT_FOUND)

        return Response(OrderSerializer(order, context={"request": request}).data)
