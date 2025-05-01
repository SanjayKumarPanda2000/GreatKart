from django.shortcuts import render
from store.models import Product,ReviewRating
import datetime
from django.utils import timezone;
def home(request):
    print(datetime.datetime.now())
    print(timezone.now())
    products=Product.objects.all().filter(is_available=True).order_by('-created_date')
    
    # for product in products:
    #     reviews=ReviewRating.objects.filter(product_id=product.id, status=True)

    context={
        'products':products
    }
    return render(request,'home.html',context)