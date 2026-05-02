# from rest_framework import serializers
# from django.templatetags.static import static
# from .models import Product
#
# class ProductSerializer(serializers.ModelSerializer):
#     image_url = serializers.SerializerMethodField()
#     category_name = serializers.CharField(source='category.name', read_only=True)
#
#     class Meta:
#         model = Product
#         fields = [
#             'id', 'name', 'stock', 'price', 'category', 'category_name',
#             'image_static_path', 'image_url'
#         ]
#
#     def get_image_url(self, obj):
#         if not obj.image_static_path:
#             return None
#         url = static(obj.image_static_path)  # builds /static/products/...
#         request = self.context.get('request')
#         return request.build_absolute_uri(url) if request else url




from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'stock', 'price',
            'category', 'category_name',
            'image', 'image_url',   # keep only fields that exist on the model
        ]

    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            url = obj.image.url
            if url.startswith('http'):
                return url
            request = self.context.get('request')
            return request.build_absolute_uri(url) if request else url
        return None


class ProductBulkUpdateItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    stock = serializers.IntegerField(required=False, min_value=0)
    price = serializers.DecimalField(required=False, max_digits=10, decimal_places=2)

class ProductBulkUpdateSerializer(serializers.Serializer):
    items = ProductBulkUpdateItemSerializer(many=True)

    def validate(self, data):
        if not data.get("items"):
            raise serializers.ValidationError({"items": "At least one item is required."})
        return data