from django.shortcuts import render,redirect,get_object_or_404
from store.models import Product,Variation
from .models import Cart,CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
# Create your views here.
def _cart_id(request):
    cart=request.session.session_key
    if not cart:
        cart=request.session.create()

    return cart

def add_cart(request, product_id):
    current_user=request.user
    product = Product.objects.get(id=product_id)

    #if user is authenticated
    if current_user.is_authenticated:
        product_variation = []

        if request.method == 'POST':
            for key in request.POST:
                value = request.POST[key]
                try:
                    variation = Variation.objects.filter(
                        product=product,
                        variation_category__iexact=key,
                        variation_value__iexact=value
                    ).first()
                    if variation:
                        product_variation.append(variation)
                except:
                    pass

        

        # Check if the cart item exists
        is_cart_item_exist = CartItem.objects.filter(product=product, user=current_user).exists()

        if is_cart_item_exist:
            cart_items = CartItem.objects.filter(product=product, user=current_user)

            # Check existing variations
            ex_var_list = []
            id = []
            for item in cart_items:
                existing_variations = list(item.variations.all())
                ex_var_list.append(existing_variations)
                id.append(item.id)

            if product_variation in ex_var_list:
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(id=item_id)
                item.quantity += 1
                item.save()
            else:
                cart_item = CartItem.objects.create(product=product, user=current_user, quantity=1)
                if len(product_variation) > 0:
                    cart_item.variations.set(product_variation)
                cart_item.save()
        else:
            cart_item = CartItem.objects.create(product=product, user=current_user, quantity=1)
            if len(product_variation) > 0:
                cart_item.variations.set(product_variation)
            cart_item.save()

        return redirect('cart')
    #if user is not authenticated
    else:
        product_variation = []

        if request.method == 'POST':
            for key in request.POST:
                value = request.POST[key]
                try:
                    variation = Variation.objects.filter(
                        product=product,
                        variation_category__iexact=key,
                        variation_value__iexact=value
                    ).first()
                    if variation:
                        product_variation.append(variation)
                except:
                    pass

        # Get or create cart
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))

        # Check if the cart item exists
        is_cart_item_exist = CartItem.objects.filter(product=product, cart=cart).exists()

        if is_cart_item_exist:
            cart_items = CartItem.objects.filter(product=product, cart=cart)

            # Check existing variations
            ex_var_list = []
            id = []
            for item in cart_items:
                existing_variations = list(item.variations.all())
                ex_var_list.append(existing_variations)
                id.append(item.id)

            if product_variation in ex_var_list:
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(id=item_id)
                item.quantity += 1
                item.save()
            else:
                cart_item = CartItem.objects.create(product=product, cart=cart, quantity=1)
                if len(product_variation) > 0:
                    cart_item.variations.set(product_variation)
                cart_item.save()
        else:
            cart_item = CartItem.objects.create(product=product, cart=cart, quantity=1)
            if len(product_variation) > 0:
                cart_item.variations.set(product_variation)
            cart_item.save()

        return redirect('cart')
#for decreasing the quantity
def remove_cart(request,product_id,cart_item_id):
    product=get_object_or_404(Product,id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item=CartItem.objects.get(product=product,user=request.user,id=cart_item_id)
        else:
            cart=Cart.objects.get(cart_id=_cart_id(request))
            cart_item=CartItem.objects.get(product=product,cart=cart,id=cart_item_id)

        if cart_item.quantity > 1:
            cart_item.quantity -=1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')

#remove the item completely from the cart
def remove_cart_item(request,product_id,cart_item_id):
    product=get_object_or_404(Product,id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item=CartItem.objects.get(product=product,user=request.user,id=cart_item_id)
        else:
            cart=Cart.objects.get(cart_id=_cart_id(request))
            cart_item=CartItem.objects.get(product=product,cart=cart,id=cart_item_id)
        cart_item.delete()
    except:
        pass
    return redirect('cart')

def cart(request):
    total = 0
    quantity = 0
    cart_items = []
    tax=0
    grand_total=0.0
    try:
        if request.user.is_authenticated:
            cart_items=CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart=Cart.objects.get(cart_id=_cart_id(request))
            cart_items=CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price*cart_item.quantity)
            quantity += cart_item.quantity

        tax=2*total/100
        grand_total=total+tax
    except ObjectDoesNotExist:
        pass

    context={
        'cart_items':cart_items,
        'total_price':total,
        'total_quantity':quantity,
        'tax':tax,
        'grand_total':grand_total
    }
    return render(request,'store/cart.html',context)

@login_required(login_url='login')
def checkout(request):
    total = 0
    quantity = 0
    cart_items = []
    tax=0
    grand_total=0.0
    try:
        if request.user.is_authenticated:
            cart_items=CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart=Cart.objects.get(cart_id=_cart_id(request))
            cart_items=CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price*cart_item.quantity)
            quantity += cart_item.quantity

        tax=2*total/100
        grand_total=total+tax
    except ObjectDoesNotExist:
        pass

    context={
        'cart_items':cart_items,
        'total_price':total,
        'total_quantity':quantity,
        'tax':tax,
        'grand_total':grand_total
    }
    return render(request,'store/checkout.html',context)