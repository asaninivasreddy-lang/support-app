from django.urls import path
from .views import (UserRegisterView, UserLoginView,AdminRegisterView,AdminLoginView)

urlpatterns = [
    path('user/register/', UserRegisterView.as_view()),
    path('user/login/', UserLoginView.as_view()),
    path('admin/register/', AdminRegisterView.as_view()),
    path('admin/login/', AdminLoginView.as_view()),
]
