from django.shortcuts import render,redirect
from django.urls import reverse
from .forms import RegistractionForm,UserForm,UserProfileForm
from .models import Account,UserProfile
from order.models import Order,OrderProduct

from django.contrib import messages
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.http import HttpResponse
import datetime
from django.utils import timezone
from .token import FiveMinuteTokenGenerator
from carts.models import Cart,CartItem
from carts.views import _cart_id
import requests
from django.contrib.auth import update_session_auth_hash
# Create your views here.
def register(request):
    if request.method=='POST':
        form=RegistractionForm(request.POST)
        if form.is_valid():
            first_name=form.cleaned_data['first_name']
            last_name=form.cleaned_data['last_name']
            email=form.cleaned_data['email']
            phone_number=form.cleaned_data['phone_number']
            password=form.cleaned_data['password']
            username=email.split("@")[0]

            if Account.objects.filter(phone_number=phone_number).exists():
                form.add_error('phone_number', 'Phone number already exists.')
            if Account.objects.filter(email=email).exists():
                form.add_error('email', 'Email already exists.')
            else:
                user = Account.objects.create_user(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    username=username,
                    password=password,
                    phone_number=phone_number
                )
                user.is_active = False  # Set to True if you want to allow immediate login
                user.save()

                #User Authentication
                current_site=get_current_site(request)
                mail_subject="Please Activate Your Account"
                message=render_to_string('accounts/account_verification_email.html',{
                    'user':user,
                    'domain':current_site.domain,
                    'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                    'token':default_token_generator.make_token(user),
                })
                
                to_email=email
                email = EmailMessage(mail_subject, message, to=[to_email])
                email.send()

                # messages.success(request, "A varification link is sent to your registered mail. Please veryfy it")
                login_url = reverse('login')  # or 'accounts:login' if it's namespaced
                redirect_url = f"{login_url}?command=verification&email={to_email}"
                return redirect(redirect_url)
    else:
        form=RegistractionForm()

    context={
        'form':form
    }
    return render(request,'accounts/register.html',context)

def login(request):
    if request.method=="POST":
        email=request.POST['email']
        password=request.POST['password']

        user=auth.authenticate(email=email,password=password)

        if user is not None:
            try:
                cart=Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists=CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item=CartItem.objects.filter(cart=cart)

                    #getting the roduct variation by cart id
                    product_variation = []
                    for item in cart_item:
                        variation=item.variations.all()
                        product_variation.append(list(variation))

                    #get the cart item item from the user to access his product variation
                    cart_items = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id = []
                    for item in cart_items:
                        existing_variations = list(item.variations.all())
                        ex_var_list.append(existing_variations)
                        id.append(item.id)

                    for pr in product_variation:
                        if pr in ex_var_list:
                            index=ex_var_list.index(pr)
                            item_id=id[index]
                            item=CartItem.objects.get(id=item_id)
                            item.quantity +=1
                            item.user=user
                            item.save()
                        else:
                            cart_item=CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user=user
                                item.save()  

                     
            except:
                pass
            auth.login(request,user)
            messages.success(request,"you are logged in.")
            url=request.META.get('HTTP_REFERER')
            try:
                query=requests.utils.urlparse(url).query
                #next=cart/checkout
                params=dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage=params['next']
                    return redirect(nextPage)
            except:
                return redirect('dashboard')
        else:
            messages.error(request,"Invalid Login Cradential")
            return redirect('login')
        
    return render(request,'accounts/login.html')

@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request,"You are Logged Out!")
    return redirect('login')


def activate(request,uidb64,token):
    try:
        uid=force_str(urlsafe_base64_decode(uidb64))
        user=Account.objects.get(id=uid)
        print(f'decoded user ID: {user.id}')
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user=None
    if user.is_active:
        messages.info(request, 'Account already activated.')
        return redirect('login')
    if user and not user.is_active:
        if default_token_generator.check_token(user,token):
            user.is_active=True
            user.save()
            messages.success(request,'Your account has been activated successfully. You can now log in.')
            return redirect('login')
        else:
            messages.error(request, 'Activation link is invalid!')
            return redirect('register')
    else:
        messages.info(request, 'Account already activated.')
        return redirect('login')
    


@login_required(login_url='login')    
def dashboard(request):
    order=Order.objects.filter(user=request.user,is_ordered=True)
    order_count=order.count()
    user_profile=UserProfile.objects.get(user_id=request.user.id)
    context={
        'order_count':order_count,
        'userprofile':user_profile
    }
    return render(request,'accounts/dashboard.html',context)



def forgotpassword(request):
    if request.method == 'POST':
        email=request.POST['email']

        #check this email is valid or not
        if Account.objects.filter(email=email).exists():
            user=Account.objects.get(email__exact=email)

            #reset password email 
            #User Authentication
            current_site=get_current_site(request)
            mail_subject="Reset Your Password"
            message=render_to_string('accounts/reset_password_email.html',{
                'user':user,
                'domain':current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            to_email=email
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()

            messages.success(request, 'Password reset email has been sent to your email address')
            return redirect('login')

        else:
            messages.error(request,"Invalid email Id")
            return redirect('forgotpassword')
    return render(request,'accounts/forgotpassword.html')

def resetpassword_validate(request,uidb64,token):
    try:
        uid=force_str(urlsafe_base64_decode(uidb64))
        user=Account.objects.get(id=uid)
        print(f'decoded user ID: {user.id}')
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user=None

    if user is not None and default_token_generator.check_token(user,token):
        request.session['uid']=uid
        messages.success(request,'Please reset your password')
        return redirect('resetpassword')
    else:
        messages.error(request,'This link has been expired')
        return redirect('login')
    
def resetpassword(request):
    if request.method=='POST':
        password=request.POST['password']
        confirm_password=request.POST['confirm_password']

        if password == confirm_password:
            uid=request.session.get('uid')
            user=Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request,'Password Reset successfully.')
            return redirect('login')
        else:
            messages.error(request,'password do not metch')
            return redirect('resetpassword')
    return render(request,'accounts/resetpassword.html')

@login_required(login_url='/login/')
def my_orders(request):
    orders=Order.objects.filter(user=request.user,is_ordered=True).order_by('-created_at')
    
    # Optional: prefetch order items to avoid N+1 queries
    
    
    for order in orders:
        order.order_items = OrderProduct.objects.filter(order=order)
        subtotal = 0
        for item in order.order_items:
            item.total_price = item.quantity * item.product_price
            subtotal += item.total_price
        
        order.subtotal = subtotal  # Add subtotal to each order
    
    context={
        'orders':orders,
    }
    return render(request,'accounts/my_orders.html',context)

@login_required(login_url='/login/')
def edit_profile(request):
    try:
        user_profile=UserProfile.objects.get(user=request.user)
        
    except UserProfile.DoesNotExist:
        user_profile=None
    
    if request.method=='POST':
        user_form=UserForm(request.POST, instance=request.user)
        profile_form=UserProfileForm(request.POST,request.FILES, instance=user_profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request,"Your profile has been updated")
            return redirect('edit_profile')
    
    context={
        'userprofile':user_profile
    }
    return render(request,'accounts/edit_profile.html', context)

@login_required(login_url='/login/')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        if not user.check_password(current_password):
            messages.error(request, 'Your current password is incorrect.')
            return redirect('change_password')

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('change_password')

        if len(new_password) < 8:
            messages.warning(request, 'Password must be at least 8 characters.')
            return redirect('change_password')

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)  # Keep the user logged in
        messages.success(request, 'Your password has been successfully updated.')
        return redirect('dashboard') 
    return render(request,'accounts/change_password.html')