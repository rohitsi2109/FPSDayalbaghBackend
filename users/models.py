# from django.db import models
# from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
#
#
# class UserManager(BaseUserManager):
#     def create_user(self, phone, name, password=None, **extra_fields):
#         if not phone:
#             raise ValueError("Phone number is required")
#         if not name:
#             raise ValueError("Name is required")
#         user = self.model(phone=phone, name=name, **extra_fields)
#         user.set_password(password)
#         user.save(using=self._db)
#         return user
#
#     def create_superuser(self, phone, name, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#         extra_fields.setdefault('is_active', True)
#         return self.create_user(phone, name, password, **extra_fields)
#
#
# class User(AbstractBaseUser, PermissionsMixin):
#     phone = models.CharField(max_length=10, unique=True)
#     name = models.CharField(max_length=100)
#     gender = models.CharField(max_length=10, blank=True, null=True)
#     address = models.TextField(blank=True)
#     is_active = models.BooleanField(default=True)
#     is_staff = models.BooleanField(default=False)
#
#     USERNAME_FIELD = 'phone'
#     REQUIRED_FIELDS = ['name']
#
#     objects = UserManager()
#
#     def __str__(self):
#         return self.phone




from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, phone, name, address, password=None, **extra_fields):
        if not phone:
            raise ValueError('Phone is required')
        user = self.model(phone=phone, name=name, address=address, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, name, address, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone, name, address, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=100)
    address = models.TextField()
    gender = models.CharField(max_length=10, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['name', 'address']

    def __str__(self):
        return self.phone
