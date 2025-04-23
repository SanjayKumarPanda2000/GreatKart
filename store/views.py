from django.shortcuts import render,get_object_or_404
from .models import Product
from category.models import Category
from carts.models import CartItem,Cart
from carts.views import _cart_id
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.db.models import Q
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

    context={
        'product':product,
        'in_cart':in_cart,
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