from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from products.models import Product
from .models import Order, OrderItem, OrderStatus


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_id = serializers.IntegerField(source="product.id", read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "product_id", "product_name", "quantity", "unit_price", "line_total", "image_url"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if getattr(obj.product, "image", None) and obj.product.image:
            url = obj.product.image.url
            return request.build_absolute_uri(url) if request else url
        return None


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "status", "status_display", "payment_method",
            "total_amount", "shipping_name", "shipping_phone",
            "address_line1", "address_line2", "city", "state", "pincode",
            "items", "created_at",
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemInputSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = [
            "payment_method",
            "shipping_name", "shipping_phone",
            "address_line1", "address_line2", "city", "state", "pincode",
            "items",
        ]

    def validate(self, attrs):
        items = attrs.get("items") or []
        if not items:
            raise serializers.ValidationError({"items": "At least one item is required."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        items_data = validated_data.pop("items")

        order = Order.objects.create(user=user, **validated_data)

        total = Decimal("0.00")

        # Lock products to avoid race conditions (concurrent orders)
        product_map = {}
        product_ids = [i["product_id"] for i in items_data]
        products = Product.objects.select_for_update().filter(id__in=product_ids)

        for p in products:
            product_map[p.id] = p

        # Validate items and build rows
        for item in items_data:
            pid = item["product_id"]
            qty = int(item["quantity"])
            product = product_map.get(pid)

            if not product:
                raise serializers.ValidationError({"items": f"Product {pid} not found."})
            if qty <= 0:
                raise serializers.ValidationError({"items": "Quantity must be >= 1."})
            if product.stock < qty:
                raise serializers.ValidationError({"items": f"Insufficient stock for {product.name}."})

        # Create order items & decrement stock
        order_items = []
        for item in items_data:
            pid = item["product_id"]
            qty = int(item["quantity"])
            product = product_map[pid]

            unit_price = Decimal(product.price)
            line_total = unit_price * qty
            total += line_total

            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=qty,
                    unit_price=unit_price,
                    line_total=line_total,
                )
            )

            # decrement stock
            product.stock -= qty
            product.save(update_fields=["stock"])

        OrderItem.objects.bulk_create(order_items)

        order.total_amount = total
        order.save(update_fields=["total_amount"])

        return order

    def to_representation(self, instance):
        # After creation, return the full order representation
        return OrderSerializer(instance, context=self.context).data





class OrderItemSerializer(serializers.ModelSerializer):
    ...
    def get_image_url(self, obj):
        try:
            f = getattr(obj.product, "image", None)
            if f and getattr(f, "url", None):
                request = self.context.get("request")
                return request.build_absolute_uri(f.url) if request else f.url
        except Exception:
            pass
        return None