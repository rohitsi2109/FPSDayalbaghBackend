from django.urls import path
from .views import RegisterView, LoginView, PasswordResetView

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('password-reset/', PasswordResetView.as_view()),
]
