from django.shortcuts import render,redirect
from django.http import HttpResponse,JsonResponse
from carts.models import CartItem
from django.contrib import messages
from .forms import OrderForm
from .models import Order,Payment,OrderProduct
from datetime import datetime
import json
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
# Create your views here.
def payments(request):
    body=json.loads(request.body)
    order=Order.objects.get(user=request.user, is_ordered=False,order_number=body['orderID'])

    payment=Payment(
        user=request.user,
        payment_id=body['transID'],
        payment_method=body['payment_method'],
        amount_paid=order.order_total,
        status=body['status']
    )
    payment.save()

    #modify the order table
    order.payment=payment
    order.is_ordered=True
    order.save()

    #move the cart items to the order product table
    cart_items=CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderedproduct=OrderProduct()
        orderedproduct.order_id=order.id
        orderedproduct.payment=payment
        orderedproduct.user_id=request.user.id
        orderedproduct.product_id=item.product_id
        orderedproduct.quantity=item.quantity
        orderedproduct.product_price=item.product.price
        orderedproduct.ordered=True
        orderedproduct.save()

        cart_item=CartItem.objects.get(id=item.id)
        product_variations=cart_item.variations.all()
        orderedproduct=OrderProduct.objects.get(id=orderedproduct.id)
        orderedproduct.variations.set(product_variations)
        orderedproduct.save()

        #reduce the quantity of the sold products
        product=Product.objects.get(id=item.product.id)
        product.stock -= item.quantity
        product.save()

    #clear cart
    CartItem.objects.filter(user=request.user).delete()

    #send the confirmation email to user email
    mail_subject="Order Confirmation"
    message=render_to_string('orders/order_received_email.html',{
        'user':request.user,
        'order':order,
        
    })
    to_email=request.user.email
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.content_subtype = 'html'
    email.send()
    
    #send order number and transition id back to sendData method via JSONResponse
    data={
        'order_number':order.order_number,
        'transID':payment.payment_id,
    }

    return JsonResponse(data)

def place_order(request):
    current_user=request.user

    #if cart is empty then redirect to store page for adding item in cart
    cart_items=CartItem.objects.filter(user=current_user)
    item_count=cart_items.count()
    if item_count <= 0:
        messages.warning(request,"Cart is empty. For order add some items.")
    

    total=0
    quantity=0
    grand_total=0
    tax=0

    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity +=cart_item.quantity

    tax=(2 * total)/100
    grand_total=total + tax

    if request.method=='POST':
        form=OrderForm(request.POST)
        if form.is_valid():
            #store all the billing details inside order table
            data=Order()
            data.user=current_user
            data.first_name=form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address = form.cleaned_data['address']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.pincode=form.cleaned_data['pincode']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Generate unique order number (e.g., 20250425XXXX)
            today = datetime.now().strftime('%Y%m%d')  # e.g., 20250425
            order_number = today + str(data.id).zfill(4)  # ensure it's padded
            data.order_number = order_number
            data.save()

            order=Order.objects.get(user=current_user,is_ordered=False,order_number=order_number)
           
            context={
                'order':order,
                'cart_items':cart_items,
                'total':total,
                'tax':tax,
                'grand_total':grand_total
            }
            return render(request, 'orders/payments.html', context)
        else:
            print('inside else')
            return redirect('checkout')
        
def order_complete(request):
    order_number=request.GET['order_number']
    transID=request.GET['payment_id']
    
    try:
        order=Order.objects.get(order_number=order_number, is_ordered=True)
        orderedproducts=OrderProduct.objects.filter(order_id=order.id)
        
        subtotal=0
        for item in orderedproducts:
            subtotal += (item.product.price * item.quantity)
        
        payment=Payment.objects.get(payment_id=transID,)
        context={
            'order':order,
            'order_product':orderedproducts,
            'payment':payment,
            'subtotal':subtotal
        }
        return render(request,'orders/order_complete.html',context)
    except(): 
        return redirect('home')  
    