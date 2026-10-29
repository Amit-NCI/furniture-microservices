
from django.db import IntegrityError, transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Order, OrderIdempotencyKey
from .authentication import JWTTokenAuthentication
from .publisher import publish_order_placed


# ================= CREATE ORDER =================
class CreateOrder(APIView):
    authentication_classes = [JWTTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)

        if (
            isinstance(product_id, bool)
            or not isinstance(product_id, int)
            or product_id <= 0
        ):
            return Response(
                {'error': 'product_id must be a positive integer'},
                status=400
            )

        if (
            isinstance(quantity, bool)
            or not isinstance(quantity, int)
            or quantity <= 0
        ):
            return Response(
                {'error': 'quantity must be a positive integer'},
                status=400
            )

        key = request.headers.get('Idempotency-Key')

        if key is not None:
            if not key or len(key) > 128 or not key.isascii() or not key.isprintable():
                return Response(
                    {'error': 'Invalid Idempotency-Key'},
                    status=400
                )

        user_id = request.user.id

        # Preserve existing Add to Cart behavior when no key is supplied.
        if key is None:
            order = Order.objects.create(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity,
                status='cart'
            )
            return Response(
                {
                    'message': 'Item added to cart',
                    'order_id': order.id
                },
                status=200
            )

        # Reuse an existing order when the same customer repeats a key.
        existing = OrderIdempotencyKey.objects.filter(
            user_id=user_id,
            key=key,
        ).first()

        if existing is not None:
            if (
                existing.product_id != product_id
                or existing.quantity != quantity
            ):
                return Response(
                    {'error': 'Idempotency key already used with different request details'},
                    status=409
                )

            return Response(
                {
                    'message': 'Item added to cart',
                    'order_id': existing.order_id
                },
                status=200
            )

        # Create the order and claim the key in one transaction.
        # A uniqueness conflict rolls back the newly created order.
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user_id=user_id,
                    product_id=product_id,
                    quantity=quantity,
                    status='cart'
                )

                OrderIdempotencyKey.objects.create(
                    user_id=user_id,
                    key=key,
                    product_id=product_id,
                    quantity=quantity,
                    order=order,
                )

        except IntegrityError:
            # Another request may have claimed this key concurrently.
            existing = OrderIdempotencyKey.objects.get(
                user_id=user_id,
                key=key,
            )

            if (
                existing.product_id != product_id
                or existing.quantity != quantity
            ):
                return Response(
                    {'error': 'Idempotency key already used with different request details'},
                    status=409
                )

            return Response(
                {
                    'message': 'Item added to cart',
                    'order_id': existing.order_id
                },
                status=200
            )

        return Response(
            {
                'message': 'Item added to cart',
                'order_id': order.id
            },
            status=200
        )


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
            try:
                publish_order_placed(
                    order_id=order.id,
                    user_id=str(request.user.id),
                    items=[{
                        'product_id': order.product_id,
                        'quantity': order.quantity,
                        'product_name': order.product_name,
                    }]
                )
            except Exception:
                # Event delivery is best-effort — the order is already
                # placed and is the source of truth. A RabbitMQ outage
                # must not fail the customer's checkout.
                pass

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