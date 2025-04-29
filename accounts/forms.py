from django import forms
from .models import Account, UserProfile
from django.core.exceptions import ValidationError

class RegistractionForm(forms.ModelForm):
    password=forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder':'Enter Password'
    }))
    confirm_password=forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder':'Confirm Password'
    }))
    class Meta:
        model = Account
        fields=['first_name','last_name','email','phone_number','password']

    def __init__(self,*args,**kwargs):
        super(RegistractionForm,self).__init__(*args,**kwargs)
        self.fields['first_name'].widget.attrs['placeholder']='Enter First Name'
        self.fields['last_name'].widget.attrs['placeholder']='Enter Last Name'
        self.fields['email'].widget.attrs['placeholder']='Enter Email'
        self.fields['phone_number'].widget.attrs['placeholder']='Enter Phone Number'
        for field in self.fields:
            self.fields[field].widget.attrs['class']='form-control'
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match")

        return cleaned_data

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if Account.objects.filter(phone_number=phone_number).exists():
            raise ValidationError("Phone number already exists")
        return phone_number
    

class UserForm(forms.ModelForm):
    class Meta:
        model = Account
        fields=('first_name','last_name','email','phone_number')
        
        
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields=('address','profile_picture','city','state','country')