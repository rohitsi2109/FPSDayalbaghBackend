# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from django.contrib.auth import authenticate
# from .models import User
# from users.serializers import RegisterSerializer, LoginSerializer, UserSerializer
# from rest_framework.authtoken.models import Token
# from django.shortcuts import render
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from .serializers import RegisterSerializer
# from django.views.decorators.csrf import ensure_csrf_cookie
# from django.utils.decorators import method_decorator
#
#
# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class CSRFTokenView(APIView):
#     def get(self, request):
#         return Response({"message": "CSRF cookie set."})
#
#
# def home_view(request):
#     return render(request, 'index.html')
#
#
# class RegisterView(APIView):
#     def post(self, request):
#         serializer = RegisterSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({'message': 'User created successfully'}, status=201)
#         print(serializer.errors)  # 👈 Add this line
#         return Response(serializer.errors, status=400)
#
#
# # class LoginView(APIView):
# #     def post(self, request):
# #         serializer = LoginSerializer(data=request.data)
# #         if serializer.is_valid():
# #             phone = serializer.validated_data['phone']
# #             password = serializer.validated_data['password']
# #             user = authenticate(phone=phone, password=password)
# #             if user:
# #                 token, _ = Token.objects.get_or_create(user=user)
# #                 return Response({'token': token.key}, status=status.HTTP_200_OK)
# #             return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
# #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# class LoginView(APIView):
#     permission_classes = [AllowAny]
#
#     def post(self, request):
#         serializer = LoginSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         phone = serializer.validated_data['phone']
#         password = serializer.validated_data['password']
#
#         # requires an auth backend that supports phone+password
#         user = authenticate(request, phone=phone, password=password)
#         if not user:
#             return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
#
#         token, _ = Token.objects.get_or_create(user=user)
#
#         # optional but useful
#         user.last_login = timezone.now()
#         user.save(update_fields=['last_login'])
#
#         return Response(
#             {
#                 'token': token.key,
#                 'user': UserSerializer(user).data,
#             },
#             status=status.HTTP_200_OK
#         )
#
# # views.py
# from django.shortcuts import render
# from django.utils import timezone
# from django.views.decorators.csrf import ensure_csrf_cookie
# from django.utils.decorators import method_decorator
# from django.contrib.auth import authenticate
#
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import AllowAny
# from rest_framework.authtoken.models import Token
#
# from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
#
#
# @method_decorator(ensure_csrf_cookie, name='dispatch')
# class CSRFTokenView(APIView):
#     permission_classes = [AllowAny]
#
#     def get(self, request):
#         return Response({"message": "CSRF cookie set."}, status=status.HTTP_200_OK)
#
#
# def home_view(request):
#     return render(request, "index.html")
#
#
# class RegisterView(APIView):
#     permission_classes = [AllowAny]
#
#     def post(self, request):
#         serializer = RegisterSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
#
#
# class LoginView(APIView):
#     permission_classes = [AllowAny]
#
#     def post(self, request):
#         serializer = LoginSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         phone = serializer.validated_data["phone"]
#         password = serializer.validated_data["password"]
#
#         # Requires an auth backend that accepts phone+password
#         user = authenticate(request, phone=phone, password=password)
#         if not user:
#             return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
#
#         token, _ = Token.objects.get_or_create(user=user)
#
#         # Optional: keep last_login fresh
#         user.last_login = timezone.now()
#         user.save(update_fields=["last_login"])
#
#         return Response(
#             {
#                 "token": token.key,
#                 "user": UserSerializer(user).data,
#             },
#             status=status.HTTP_200_OK,
#         )
#
#
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"message": "CSRF cookie set."}, status=status.HTTP_200_OK)


def home_view(request):
    return render(request, "index.html")


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
        else:
            print("Register Validation Errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        password = serializer.validated_data["password"]

        user = authenticate(request, phone=phone, password=password)
        if not user:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        token, _ = Token.objects.get_or_create(user=user)

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        return Response(
            {"token": token.key, "user": UserSerializer(user).data},
            status=status.HTTP_200_OK,
        )


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get('phone')
        new_password = request.data.get('new_password')

        if not phone or not new_password:
            return Response({"error": "Phone and new_password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from .models import User
            user = User.objects.get(phone=phone)
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User with this phone number does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
