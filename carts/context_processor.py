from .models import Cart,CartItem
from .views import _cart_id

def counter(request):
    cart_count = 0
    if 'admin' in request.path:
        return {}
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user)
            print(f'User is authenticated, cart items: {cart_items}')
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart)
            print(f'Anonymous user, cart items: {cart_items}')

        for item in cart_items:
            cart_count += item.quantity

    except Cart.DoesNotExist:
        print('Cart does not exist')
        cart_count = 0

    return dict(cart_count=cart_count)
