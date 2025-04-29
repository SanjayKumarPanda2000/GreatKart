from django.shortcuts import render,get_object_or_404,redirect
from .models import Product, ReviewRating
from category.models import Category
from carts.models import CartItem,Cart
from carts.views import _cart_id
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.db.models import Q
from .forms import ReviewForm
from django.contrib import messages
from order.models import OrderProduct
# Create your views here.
def store(request,category_slug=None):
    categories=None
    products=None
    if category_slug != None:
        categories=get_object_or_404(Category,slug=category_slug)
        products=Product.objects.filter(category=categories).order_by('id')
        #pagination logic
        paginator=Paginator(products,3)
        page=request.GET.get('page')
        page_products=paginator.get_page(page)
    else:
        products=Product.objects.all().filter(is_available=True).order_by('id')
        #pagination logic
        paginator=Paginator(products,3)
        page=request.GET.get('page')
        page_products=paginator.get_page(page)
        
    product_count=products.count()
    context={
        'products':page_products,
        'product_count':product_count
    }
    return render(request,'store/store.html',context)

def product_details(request,category_slug,product_slug):
    try:
        product=Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart=CartItem.objects.filter(cart__cart_id=_cart_id(request),product=product).exists()

    
    except Exception as e:
        raise e
    
    if request.user.is_authenticated:
        try:
            orderproduct=OrderProduct.objects.filter(user=request.user,product=product).exists
        except OrderProduct.DoesNotExist:
            orderproduct=None
    else:
        orderproduct=None
    
    reviews=ReviewRating.objects.filter(product_id=product.id, status=True)    
    
    context={
        'product':product,
        'in_cart':in_cart,
        'orderproduct':orderproduct,
        'reviews':reviews
    }
    return render(request,'store/product_details.html',context)

def search(request):
    products = []
    product_count = 0
    if 'keyword' in request.GET:
        keyword=request.GET['keyword']
        if keyword:
            products=Product.objects.order_by('created_date').filter(Q(description__icontains=keyword) | 
                                                                     Q(product_name__icontains=keyword))
            product_count=products.count()
        
    #pagination logic
    paginator=Paginator(products,3)
    page=request.GET.get('page')
    page_products=paginator.get_page(page)
    context={
        'products':page_products,
        'product_count':product_count
    }
    return render(request,'store/store.html',context)

def submit_review(request,product_id):
    url=request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            review=ReviewRating.objects.get(user__id=request.user.id,product__id=product_id)
            form=ReviewForm(request.POST,instance=review)
            form.save()
            messages.success(request,'Thank You! Your review has been updated')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form=ReviewForm(request.POST)
            if form.is_valid():
                data=ReviewRating()
                data.subject=form.cleaned_data['subject']
                data.review=form.cleaned_data['review']
                data.rating=form.cleaned_data['rating']
                data.ip=request.META.get('REMOTE_ADDR')
                data.user_id=request.user.id
                data.product_id=product_id
                data.save()
                messages.success(request,'Thank You! Your review has been submited')
                return redirect(url)