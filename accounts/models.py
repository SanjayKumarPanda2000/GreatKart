from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager

#create ModelManager for the CustomUser model
class MyAccountManager(BaseUserManager):
    def create_user(self,first_name,last_name,username,email,phone_number,password):
        if not email:
            raise ValueError("User Must Have an email address")
        if not username:
            raise ValueError('User must have an username')
        
        user=self.model(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=self.normalize_email(email),
            phone_number=phone_number
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self,first_name,last_name,username,email,password):
        user=self.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=self.normalize_email(email),
            password=password
        )

        user.is_admin=True
        user.is_staff=True
        user.is_active=True
        user.is_superadmin=True

        user.save(using=self._db)
        return user
    

# Create your models here.
class Account(AbstractBaseUser):
    first_name=models.CharField(max_length=50)
    last_name=models.CharField(max_length=50)
    username=models.CharField(max_length=50,unique=True)
    email=models.EmailField(max_length=100,unique=True)
    phone_number=models.CharField(max_length=10,unique=True)

    #Required fields
    date_joined=models.DateTimeField(auto_now_add=True)
    last_login=models.DateTimeField(auto_now=True)
    is_admin=models.BooleanField(default=False)
    is_staff=models.BooleanField(default=False)
    is_active=models.BooleanField(default=False)
    is_superadmin=models.BooleanField(default=False)

    USERNAME_FIELD='email'
    REQUIRED_FIELDS=['first_name','last_name','username']

    objects=MyAccountManager()
    
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.email
    
    def has_perm(self,perm,obj=None):
        return self.is_admin
    
    def has_module_perms(self,add_lebel):
        return True
    
class UserProfile(models.Model):
    user=models.OneToOneField(Account, on_delete=models.CASCADE)
    address=models.CharField(blank=True, max_length=100)
    profile_picture=models.ImageField(blank=True, upload_to='userprofile/')
    city=models.CharField(blank=True,max_length=20)
    state=models.CharField(blank=True,max_length=20)
    country=models.CharField(blank=True,max_length=20)
    
    def __str__(self):
        return self.user.first_name