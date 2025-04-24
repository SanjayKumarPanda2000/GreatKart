from django.shortcuts import render
from store.models import Product
import datetime
from django.utils import timezone;
def home(request):
    print(datetime.datetime.now())
    print(timezone.now())
    products=Product.objects.all().filter(is_available=True)

    context={
        'products':products
    }
    return render(request,'home.html',context)