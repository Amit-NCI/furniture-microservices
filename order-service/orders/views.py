
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Order
from .authentication import JWTTokenAuthentication
from .publisher import publish_order_placed


# ================= CREATE ORDER =================
class CreateOrder(APIView):
    authentication_classes = [JWTTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        Order.objects.create(
            user_id=request.user.id,
            product_id=data.get('product_id'),
            quantity=data.get('quantity', 1),
            status=data.get('status', 'cart')
        )
        return Response({'message': 'Item added to cart'})


# ================= GET USER ORDERS =================
class GetUserOrders(APIView):
    authentication_classes = [JWTTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        orders = Order.objects.filter(
            user_id=request.user.id
        ).values()
        return Response(list(orders))


# ================= CART LIST =================
class CartList(APIView):
    authentication_classes = [JWTTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(
            user_id=request.user.id,
            status='cart'
        )
        return Response(list(orders.values()))


# ================= CHECKOUT =================
# ================= CHECKOUT =================
class Checkout(APIView):
    authentication_classes = [JWTTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):

        selected_ids = request.data.get('items', [])

        if not selected_ids:
            return Response({'error': 'No items selected'}, status=400)

        cart_items = Order.objects.filter(
            user_id=request.user.id,
            status='cart',
            id__in=selected_ids
        )

        if not cart_items.exists():
            return Response({'error': 'Selected items not found'}, status=404)

        # Mark items as placed FIRST — this is the source of truth
        cart_items.update(status='placed')

        # Build event payload
        items_payload = [
            {
                'product_id': item.product_id,
                'quantity': item.quantity,
                'product_name': item.product_name,
            }
            for item in cart_items
        ]

        # Publish event — failure here does NOT affect the checkout response
        # Product service will decrement stock when it receives the event
        placed_orders = Order.objects.filter(
            user_id=request.user.id,
            status='placed',
            id__in=selected_ids
        )
        for order in placed_orders:
            publish_order_placed(
                order_id=order.id,
                user_id=str(request.user.id),
                items=[{
                    'product_id': order.product_id,
                    'quantity': order.quantity,
                    'product_name': order.product_name,
                }]
            )

        return Response({'message': 'Order placed successfully'})


# ================= ORDER HISTORY =================
class OrderHistory(APIView):
    authentication_classes = [JWTTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        orders = Order.objects.filter(
            user_id=request.user.id
        ).exclude(status='cart')
        return Response(list(orders.values()))


# ================= DELETE CART ITEM =================
class DeleteCartItem(APIView):
    authentication_classes = [JWTTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, order_id):
        try:
            order = Order.objects.get(
                id=order_id,
                status='cart',
                user_id=request.user.id
            )
            order.delete()
            return Response({'message': 'Item removed from cart'})
        except Order.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)


# ================= UPDATE QUANTITY =================
class UpdateQuantity(APIView):
    authentication_classes = [JWTTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(
                id=order_id,
                status='cart',
                user_id=request.user.id
            )
            action = request.data.get('action')

            if action == 'increase':
                order.quantity += 1
            elif action == 'decrease':
                if order.quantity > 1:
                    order.quantity -= 1

            order.save()
            return Response({
                'message': 'Quantity updated',
                'quantity': order.quantity
            })
        except Order.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)


# ================= REMOVE SELECTED ITEMS =================
class RemoveSelectedItems(APIView):
    authentication_classes = [JWTTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        item_ids = request.data.get('items', [])

        if not item_ids:
            return Response({'error': 'No items selected'}, status=400)

        deleted, _ = Order.objects.filter(
            user_id=request.user.id,
            status='cart',
            id__in=item_ids
        ).delete()
        return Response({'message': f'{deleted} item(s) removed'})


# ================= CLEAR CART =================
class ClearCart(APIView):
    authentication_classes = [JWTTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id):
        deleted, _ = Order.objects.filter(
            user_id=request.user.id,
            status='cart'
        ).delete()
        return Response({'message': f'Cart cleared ({deleted} items)'})