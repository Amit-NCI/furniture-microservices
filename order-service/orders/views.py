from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Order

# ================= CREATE ORDER =================
class CreateOrder(APIView):
    def post(self, request):
        data = request.data

        Order.objects.create(
            user_id=data.get("user_id"),
            product_id=data.get("product_id"),
            quantity=data.get("quantity", 1),
            status=data.get("status", "cart")
        )

        return Response({"message": "Item added to cart"})


# ================= GET USER ORDERS =================
class GetUserOrders(APIView):
    def get(self, request, user_id):
        orders = Order.objects.filter(user_id=user_id).values()
        return Response(list(orders))


# ================= CART LIST =================
class CartList(APIView):
    def get(self, request):
        orders = Order.objects.filter(status="cart")
        return Response(list(orders.values()))


# ================= CHECKOUT =================
class Checkout(APIView):
    def post(self, request, user_id):
        selected_ids = request.data.get("items", [])

        if not selected_ids:
            return Response({"error": "No items selected"}, status=400)

        # Get only selected cart items
        cart_items = Order.objects.filter(
            user_id=user_id,
            status='cart',
            id__in=selected_ids
        )

        if not cart_items.exists():
            return Response({"error": "Selected items not found"}, status=404)

        # ✅ Update ONLY selected items
        cart_items.update(status='placed')

        return Response({"message": "Selected items ordered successfully 🎉"})


# ================= ORDER HISTORY =================
class OrderHistory(APIView):
    def get(self, request, user_id):
        # ✅ show ALL orders except cart
        orders = Order.objects.filter(user_id=user_id).exclude(status='cart')
        return Response(list(orders.values()))

# ================= CHECKOUT VIEW (OPTIONAL) =================
# 👉 You actually don’t need this now, but keeping it clean
class CheckoutView(APIView):
    def post(self, request, user_id):
        orders = Order.objects.filter(user_id=user_id, status='cart')

        if not orders.exists():
            return Response({"error": "Cart empty"})

        # ✅ FIXED → use same status
        orders.update(status='placed')

        return Response({"message": "Checkout successful"})
    
# DELETE CART ITEM


class DeleteCartItem(APIView):
    def delete(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, status='cart')
            order.delete()
            return Response({"message": "Item removed from cart"})
        except Order.DoesNotExist:
            return Response({"error": "Item not found"}, status=404)
        
# UPDATE QUANTITY
class UpdateQuantity(APIView):
    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, status='cart')

            action = request.data.get("action")

            if action == "increase":
                order.quantity += 1
            elif action == "decrease":
                if order.quantity > 1:
                    order.quantity -= 1

            order.save()

            return Response({
                "message": "Quantity updated",
                "quantity": order.quantity
            })

        except Order.DoesNotExist:
            return Response({"error": "Item not found"}, status=404)
        
# ================= REMOVE SELECTED ITEMS =================
class RemoveSelectedItems(APIView):
    def post(self, request, user_id):
        item_ids = request.data.get("items", [])

        if not item_ids:
            return Response({"error": "No items selected"}, status=400)

        deleted, _ = Order.objects.filter(
            user_id=user_id,
            status='cart',
            id__in=item_ids
        ).delete()

        return Response({"message": f"{deleted} item(s) removed"})
    
# ================= CLEAR CART =================
class ClearCart(APIView):
    def delete(self, request, user_id):
        deleted, _ = Order.objects.filter(
            user_id=user_id,
            status='cart'
        ).delete()

        return Response({"message": f"Cart cleared ({deleted} items)"})