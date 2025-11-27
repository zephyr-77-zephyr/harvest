from rest_framework import serializers

from .models import Category, Order, OrderItem, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description")


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    seller_name = serializers.CharField(source="seller.get_full_name", read_only=True)
    rating = serializers.FloatField(source="avg_rating", read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "price",
            "stock",
            "is_featured",
            "image",
            "category",
            "seller_name",
            "rating",
        )


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ("product_name", "quantity", "price")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "status", "total", "created_at", "items")

