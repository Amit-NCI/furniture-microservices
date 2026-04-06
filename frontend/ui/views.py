from django.shortcuts import render


def home(request):
    return render(request, 'home.html')

def dashboard(request):
    return render(request, 'dashboard.html')

# ✅ ADD THIS
def cart_view(request):
    return render(request, 'cart.html')

def orders_view(request):
    return render(request, 'orders.html')


def checkout_view(request):
    return render(request, 'checkout.html')