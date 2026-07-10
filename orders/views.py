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
from django.db import transaction, IntegrityError
from django.utils.dateparse import parse_datetime, parse_date

from .models import Order, OrderItem, OrderStatus, OrderSource
from .serializers import OrderSerializer, OrderCreateSerializer, UserOrderSerializer
from products.models import Product
from products.inventory import (
    apply_delta, reserve, release, commit_reservation, InsufficientStock, Reason,
)
from django.conf import settings
from django.db.models import Q


# --- Inventory phase helpers (reservation model) --------------------------
#
# An order's items affect inventory differently depending on its status:
#
#   PENDING                      -> RESERVED  : items hold `reserved` units;
#                                               physical `stock` is untouched.
#   CONFIRMED/READY/RECEIVED/... -> COMMITTED : `stock` has been decremented;
#                                               reservation released.
#   CANCELLED                    -> FREED     : neither reserved nor deducted.
#
# Whenever an order's status crosses a phase boundary we must move every line's
# units between these buckets so inventory stays exactly consistent, no matter
# which endpoint drives the change.

def _inventory_phase(status_value):
    if status_value == OrderStatus.PENDING:
        return "RESERVED"
    if status_value == OrderStatus.CANCELLED:
        return "FREED"
    return "COMMITTED"


def _transition_order_inventory(order, old_status, new_status, user):
    """
    Move every line's units between reserved/stock buckets for a status change.

    Must be called inside an open transaction. Locks each product row. Raises
    InsufficientStock if a backward transition (e.g. un-cancelling) can't secure
    the units it needs.
    """
    old_phase = _inventory_phase(old_status)
    new_phase = _inventory_phase(new_status)
    if old_phase == new_phase:
        return

    items = list(order.items.select_related("product").all())
    if not items:
        return

    pids = [i.product_id for i in items]
    locked = {
        p.id: p
        for p in Product.objects.select_for_update().filter(id__in=pids)
    }
    ref = f"order:{order.id}"

    for item in items:
        p = locked.get(item.product_id)
        if p is None:
            continue
        qty = item.quantity

        if old_phase == "RESERVED" and new_phase == "COMMITTED":
            commit_reservation(p, qty, user=user, reference=ref)
        elif old_phase == "RESERVED" and new_phase == "FREED":
            release(p, qty)
        elif old_phase == "COMMITTED" and new_phase == "FREED":
            apply_delta(p, qty, reason=Reason.RETURN, user=user, reference=ref)
        elif old_phase == "COMMITTED" and new_phase == "RESERVED":
            apply_delta(p, qty, reason=Reason.RETURN, user=user, reference=ref)
            reserve(p, qty)
        elif old_phase == "FREED" and new_phase == "RESERVED":
            reserve(p, qty)
        elif old_phase == "FREED" and new_phase == "COMMITTED":
            apply_delta(p, -qty, reason=Reason.SALE, user=user, reference=ref)


def _adjust_item_inventory(order, product, delta, user):
    """
    Apply a per-line unit change (+add / -remove) to the right inventory bucket.

    On a PENDING order units are reserved/released; on a committed order (any
    live non-cancelled status past PENDING) physical stock is decremented/
    restored. The caller MUST already hold a lock on `product`. Raises
    InsufficientStock when there aren't enough units for an increase.
    """
    if delta == 0:
        return
    ref = f"order:{order.id}"
    if order.status == OrderStatus.PENDING:
        if delta > 0:
            reserve(product, delta)
        else:
            release(product, -delta)
    else:
        reason = Reason.SALE if delta > 0 else Reason.RETURN
        apply_delta(product, -delta, reason=reason, user=user, reference=ref)


def _filtered_queryset(request, base_qs):
    """
    Apply ?status=, ?since=, ?source=, ?date_from=, ?date_to= filters.
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

    # ?date_from=2025-08-11  (filter created_at >= date)
    date_from = request.query_params.get("date_from")
    if date_from:
        d = parse_date(date_from)
        if d:
            base_qs = base_qs.filter(created_at__date__gte=d)

    # ?date_to=2025-08-15  (filter created_at <= date)
    date_to = request.query_params.get("date_to")
    if date_to:
        d = parse_date(date_to)
        if d:
            base_qs = base_qs.filter(created_at__date__lte=d)

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

    def create(self, request, *args, **kwargs):
        """
        Idempotent order creation.

        If the client sends an `Idempotency-Key` (header or body field), a retry
        with the same key returns the ALREADY-created order (HTTP 200) instead of
        placing a duplicate. Clients that send no key keep the original behaviour.
        """
        raw = (
            request.headers.get("Idempotency-Key")
            or request.data.get("idempotency_key")
            or ""
        )
        key = str(raw).strip() or None

        def _existing_response():
            existing = Order.objects.filter(
                user=request.user, idempotency_key=key
            ).first()
            if existing:
                return Response(
                    UserOrderSerializer(
                        existing, context=self.get_serializer_context()
                    ).data,
                    status=status.HTTP_200_OK,
                )
            return None

        # Fast path: key already used -> return that order, do NOT touch stock.
        if key:
            hit = _existing_response()
            if hit is not None:
                return hit

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save(idempotency_key=key)
        except IntegrityError:
            # A concurrent request with the same key won the unique-constraint
            # race; return that order rather than erroring.
            hit = _existing_response()
            if hit is not None:
                return hit
            raise

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data),
        )

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
        with transaction.atomic():
            # Release the units this pending order was holding, then cancel.
            _transition_order_inventory(
                order, order.status, OrderStatus.CANCELLED, request.user
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
            with transaction.atomic():
                item = order.items.select_related("product").get(id=item_id)
                # Lock the product row and release its reservation (PENDING order).
                product = Product.objects.select_for_update().get(pk=item.product_id)
                _adjust_item_inventory(order, product, -item.quantity, request.user)

                lt = item.line_total
                item.delete()

                order.total_amount -= lt
                if order.total_amount < 0:
                    order.total_amount = 0
                order.save(update_fields=["total_amount"])
        except OrderItem.DoesNotExist:
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
        if quantity < 1:
            return Response({"detail": "Quantity must be at least 1."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Lock the product row first so the check-and-reserve is atomic.
                product = Product.objects.select_for_update().get(id=product_id)
                try:
                    _adjust_item_inventory(order, product, quantity, request.user)
                except InsufficientStock:
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
            with transaction.atomic():
                item = order.items.select_related("product").get(id=item_id)
                product = Product.objects.select_for_update().get(pk=item.product_id)
                diff = new_qty - item.quantity

                if diff != 0:
                    # diff > 0 needs more units (reserve); diff < 0 frees them.
                    try:
                        _adjust_item_inventory(order, product, diff, request.user)
                    except InsufficientStock:
                        return Response({"detail": "Not enough stock."}, status=status.HTTP_400_BAD_REQUEST)

                item.quantity = new_qty
                item.line_total = item.quantity * item.unit_price
                item.save(update_fields=["quantity", "line_total"])
                order.total_amount += (diff * item.unit_price)
                if order.total_amount < 0:
                    order.total_amount = 0
                order.save(update_fields=["total_amount"])
        except OrderItem.DoesNotExist:
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
        old_status = order.status
        try:
            with transaction.atomic():
                # Move inventory between reserved/stock buckets if the status
                # change crosses a phase boundary (e.g. PENDING -> CONFIRMED
                # commits the reservation as a real sale).
                _transition_order_inventory(
                    order, old_status, new_status, request.user
                )
                order.status = new_status
                order.save(update_fields=["status"])
        except InsufficientStock as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(OrderSerializer(order, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            return Response(
                {"detail": "Cannot cancel delivered/already-cancelled orders."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            # PENDING orders release their reservation; confirmed orders restore
            # the physical stock they had deducted.
            _transition_order_inventory(
                order, order.status, OrderStatus.CANCELLED, request.user
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
            with transaction.atomic():
                item = order.items.select_related("product").get(id=item_id)
                # Free the units this line held (reservation if PENDING, else stock).
                product = Product.objects.select_for_update().get(pk=item.product_id)
                _adjust_item_inventory(order, product, -item.quantity, request.user)

                lt = item.line_total
                item.delete()

                order.total_amount -= lt
                if order.total_amount < 0:
                    order.total_amount = 0
                order.save(update_fields=["total_amount"])
        except OrderItem.DoesNotExist:
            return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

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

        with transaction.atomic():
            # Convert this order's reservations into real stock decrements.
            _transition_order_inventory(
                order, order.status, OrderStatus.CONFIRMED, request.user
            )
            order.status = OrderStatus.CONFIRMED
            order.save(update_fields=["status", "total_amount"])

        return Response(OrderSerializer(order, context={"request": request}).data)

    @action(detail=True, methods=["patch"], url_path="update-amount")
    def update_amount(self, request, pk=None):
        """
        Update total_amount for orders in PENDING, CONFIRMED, or RECEIVED state.
        Body: {"total_amount": 500.00}
        """
        order = self.get_object()

        allowed = [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.RECEIVED]
        if order.status not in allowed:
            return Response(
                {"detail": "Amount can only be edited for Pending, Confirmed, or Received orders."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_total = request.data.get("total_amount")
        if new_total is None:
            return Response({"detail": "total_amount is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_total = float(new_total)
            if new_total < 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response({"detail": "total_amount must be a non-negative number."}, status=status.HTTP_400_BAD_REQUEST)

        order.total_amount = new_total
        order.save(update_fields=["total_amount"])
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
        if quantity < 1:
            return Response({"detail": "Quantity must be at least 1."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Lock the product row first so the check-and-apply is atomic.
                product = Product.objects.select_for_update().get(id=product_id)
                try:
                    _adjust_item_inventory(order, product, quantity, request.user)
                except InsufficientStock:
                    avail = product.available if order.status == OrderStatus.PENDING else product.stock
                    return Response({"detail": f"Not enough stock. Available: {avail}"},
                                    status=status.HTTP_400_BAD_REQUEST)

                existing_item = order.items.filter(product=product).first()
                if existing_item:
                    existing_item.quantity += quantity
                    existing_item.line_total = existing_item.quantity * existing_item.unit_price
                    existing_item.save(update_fields=["quantity", "line_total"])
                else:
                    unit_price = product.price  # Snapshot price
                    order.items.create(
                        product=product,
                        quantity=quantity,
                        unit_price=unit_price,
                        line_total=unit_price * quantity,
                    )

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
            with transaction.atomic():
                item = order.items.select_related("product").get(id=item_id)
                product = Product.objects.select_for_update().get(pk=item.product_id)
                diff = new_quantity - item.quantity

                if diff != 0:
                    # diff > 0 needs more units; diff < 0 frees them. PENDING
                    # orders adjust the reservation, committed orders the stock.
                    try:
                        _adjust_item_inventory(order, product, diff, request.user)
                    except InsufficientStock:
                        avail = product.available if order.status == OrderStatus.PENDING else product.stock
                        return Response({"detail": f"Not enough stock. Available: {avail}"},
                                        status=status.HTTP_400_BAD_REQUEST)

                item.quantity = new_quantity
                item.line_total = item.quantity * item.unit_price
                item.save(update_fields=["quantity", "line_total"])

                order.total_amount += (diff * item.unit_price)
                if order.total_amount < 0:
                    order.total_amount = 0
                order.save(update_fields=["total_amount"])
        except OrderItem.DoesNotExist:
            return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(OrderSerializer(order, context={"request": request}).data)
