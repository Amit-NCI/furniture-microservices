from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import Product
from .serializers import ProductSerializer
from .authentication import JWTTokenAuthentication
from .permissions import IsStaffUser, IsCustomerOrStaff


# ===============================
# PRODUCT LIST + CREATE PRODUCT
# ===============================
class ProductList(APIView):
    authentication_classes = [JWTTokenAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsCustomerOrStaff()]
        return [IsStaffUser()]

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===============================
# PRODUCT DETAIL — public
# ===============================
class ProductDetail(APIView):
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return Product.objects.get(id=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ProductSerializer(product)
        return Response(serializer.data)


# ===============================
# PRODUCT UPDATE — staff only
# ===============================
class ProductUpdate(APIView):
    authentication_classes = [JWTTokenAuthentication]
    permission_classes = [IsStaffUser]

    def put(self, request, pk):
        try:
            product = Product.objects.get(id=pk)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===============================
# PRODUCT DELETE — staff only
# ===============================
class ProductDelete(APIView):
    authentication_classes = [JWTTokenAuthentication]
    permission_classes = [IsStaffUser]

    def delete(self, request, pk):
        try:
            product = Product.objects.get(id=pk)
            product.delete()
            return Response({'message': 'Product deleted'})
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )