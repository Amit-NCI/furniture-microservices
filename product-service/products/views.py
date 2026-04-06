from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer


# Existing: list all products
class ProductList(APIView):
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


# ✅ NEW: get single product
class ProductDetail(APIView):
    def get(self, request, pk):
        try:
            product = Product.objects.get(id=pk)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        serializer = ProductSerializer(product)
        return Response(serializer.data)